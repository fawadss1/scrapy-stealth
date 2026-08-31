from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any

from ..behaviors.timing import profile_request_delay
from ..utils.core.console import console
from ..utils.telemetry.stats import StealthStats

# Per-domain adaptive spacing (seconds between requests).
_MIN_DELAY_S = 0.03
_MAX_DELAY_S = 30.0
_INITIAL_DELAY_S = 0.0
_ADDITIVE_DECREASE_S = 0.04
_SUCCESS_STREAK_BEFORE_DECREASE = 4
_429_MULTIPLIER = 2.0
_429_FLOOR_S = 1.0
_SLOW_LATENCY_S = 2.5
_SLOW_LATENCY_BUMP_S = 0.08
_BROWSER_JITTER_S = 0.06
_LATENCY_EMA_ALPHA = 0.25


def parse_retry_after(value: str | bytes | None) -> float | None:
    """Parse ``Retry-After`` as delta-seconds or HTTP-date; return seconds or ``None``."""
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        try:
            text = value.decode("ascii", errors="ignore").strip()
        except Exception:
            return None
    else:
        text = str(value).strip()
    if not text:
        return None
    try:
        return float(max(0, int(text)))
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError, OverflowError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return float(max(0.0, when.timestamp() - time.time()))


def _header_value(headers: Any, name: str) -> str | bytes | None:
    if headers is None:
        return None
    try:
        return headers.get(name) or headers.get(name.lower())
    except Exception:
        return None


@dataclass
class _ThrottleSlot:
    delay: float = _INITIAL_DELAY_S
    last_request_at: float = 0.0
    rate_limit_until: float = 0.0
    latency_ema: float = 0.0
    success_streak: int = 0


@dataclass
class ThrottleRegistry:
    """Per-domain AIMD throttle with Retry-After and latency awareness."""

    _slots: dict[tuple[str, str], _ThrottleSlot] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def reset(self) -> None:
        with self._lock:
            self._slots.clear()

    def _slot(self, domain: str, driver: str) -> _ThrottleSlot:
        key = (domain.lower(), driver)
        slot = self._slots.get(key)
        if slot is None:
            slot = _ThrottleSlot()
            self._slots[key] = slot
        return slot

    def wait(
        self,
        domain: str | None,
        driver: str,
        *,
        profile: str | None = None,
        stats: StealthStats | None = None,
    ) -> float:
        """Sleep until the domain slot allows the next request; return seconds waited."""
        if not domain:
            return 0.0

        behavioral = 0.0
        if driver in ("basic", "turbo") and profile:
            behavioral = profile_request_delay(profile)
        elif driver == "browser":
            behavioral = _BROWSER_JITTER_S

        with self._lock:
            slot = self._slot(domain, driver)
            now = time.monotonic()
            ready_at = max(
                slot.last_request_at + slot.delay,
                slot.rate_limit_until,
            )
            pacing_sleep = max(0.0, ready_at - now)
            sleep_s = max(pacing_sleep, behavioral)
            slot.last_request_at = now + sleep_s

        if sleep_s > 0:
            time.sleep(sleep_s)
            if stats is not None:
                stats.record_throttle_wait(driver, sleep_s)
        return sleep_s

    def record(
        self,
        domain: str | None,
        driver: str,
        *,
        status: int,
        latency_s: float,
        headers: Any = None,
        stats: StealthStats | None = None,
    ) -> None:
        """Update adaptive delay from response status, latency, and Retry-After."""
        if not domain:
            return

        retry_after_raw = _header_value(headers, "Retry-After")
        retry_after_s = parse_retry_after(retry_after_raw)

        with self._lock:
            slot = self._slot(domain, driver)
            now = time.monotonic()

            if latency_s > 0:
                if slot.latency_ema <= 0:
                    slot.latency_ema = latency_s
                else:
                    slot.latency_ema = (
                        _LATENCY_EMA_ALPHA * latency_s
                        + (1.0 - _LATENCY_EMA_ALPHA) * slot.latency_ema
                    )

            if status == 429:
                previous = slot.delay
                slot.delay = min(
                    _MAX_DELAY_S,
                    max(slot.delay * _429_MULTIPLIER, _429_FLOOR_S),
                )
                slot.success_streak = 0
                if retry_after_s is not None:
                    slot.rate_limit_until = max(
                        slot.rate_limit_until, now + retry_after_s
                    )
                    if stats is not None:
                        stats.record_throttle_retry_after(driver)
                if slot.delay > previous + 0.01:
                    console.info(
                        f"Throttle backing off for {domain!r} "
                        f"({driver}): {previous:.2f}s -> {slot.delay:.2f}s "
                        f"after HTTP 429"
                        + (
                            f" (Retry-After {retry_after_s:.0f}s)"
                            if retry_after_s is not None
                            else ""
                        )
                    )
                if stats is not None:
                    stats.record_throttle_rate_limit(driver)
                return

            if retry_after_s is not None and status >= 400:
                slot.rate_limit_until = max(slot.rate_limit_until, now + retry_after_s)
                if stats is not None:
                    stats.record_throttle_retry_after(driver)

            if status < 400:
                slot.success_streak += 1
                if slot.success_streak >= _SUCCESS_STREAK_BEFORE_DECREASE:
                    slot.delay = max(_MIN_DELAY_S, slot.delay - _ADDITIVE_DECREASE_S)
                    slot.success_streak = 0
                if slot.latency_ema >= _SLOW_LATENCY_S and slot.delay < _MAX_DELAY_S:
                    slot.delay = min(_MAX_DELAY_S, slot.delay + _SLOW_LATENCY_BUMP_S)


_registry = ThrottleRegistry()


def get_throttle_registry() -> ThrottleRegistry:
    return _registry
