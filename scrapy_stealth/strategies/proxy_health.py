from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field

from ..config import config
from ..utils.core.console import console
from ..utils.telemetry.stats import proxy_host_for_stats


@dataclass
class _ProxySlot:
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    cooldown_until: float = 0.0


@dataclass
class ProxyHealthRegistry:
    """In-memory success/fail tracking and per-domain circuit breaker for proxies."""

    _slots: dict[tuple[str, str], _ProxySlot] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def reset(self) -> None:
        with self._lock:
            self._slots.clear()

    def _slot(self, proxy: str, domain: str) -> _ProxySlot:
        key = (proxy, domain)
        slot = self._slots.get(key)
        if slot is None:
            slot = _ProxySlot()
            self._slots[key] = slot
        return slot

    def _refresh_cooldown(self, slot: _ProxySlot) -> None:
        now = time.monotonic()
        if slot.cooldown_until and now >= slot.cooldown_until:
            slot.cooldown_until = 0.0
            slot.consecutive_failures = 0

    def is_available(self, proxy: str, domain: str | None) -> bool:
        if not config.get("STEALTH_PROXY_HEALTH"):
            return True
        now = time.monotonic()
        with self._lock:
            if domain is None:
                for (p, _d), slot in self._slots.items():
                    if p != proxy:
                        continue
                    self._refresh_cooldown(slot)
                    if slot.cooldown_until and now < slot.cooldown_until:
                        return False
                return True
            slot = self._slot(proxy, domain)
            self._refresh_cooldown(slot)
            return not slot.cooldown_until or now >= slot.cooldown_until

    def score(self, proxy: str, domain: str | None) -> float:
        if not self.is_available(proxy, domain):
            return float("-inf")
        with self._lock:
            if domain is None:
                successes = sum(
                    slot.successes
                    for (p, _d), slot in self._slots.items()
                    if p == proxy
                )
                failures = sum(
                    slot.failures for (p, _d), slot in self._slots.items() if p == proxy
                )
            else:
                slot = self._slot(proxy, domain)
                successes, failures = slot.successes, slot.failures
        total = successes + failures
        if total == 0:
            return 0.0
        return successes / total

    def record(
        self,
        proxy: str,
        domain: str,
        *,
        success: bool,
        status: int | None = None,
        banned: bool = False,
        connection_failed: bool = False,
    ) -> bool:
        """Return ``True`` when a new per-domain cooldown is started."""
        if not config.get("STEALTH_PROXY_HEALTH"):
            return False
        threshold = int(config.get("STEALTH_PROXY_CIRCUIT_AFTER") or 3)
        cooldown_s = float(config.get("STEALTH_PROXY_COOLDOWN_S") or 300.0)
        circuit_codes = config.get("STEALTH_PROXY_CIRCUIT_CODES") or frozenset({403})

        with self._lock:
            slot = self._slot(proxy, domain)
            self._refresh_cooldown(slot)
            if success:
                slot.successes += 1
                slot.consecutive_failures = 0
                return False

            slot.failures += 1
            trips = (
                connection_failed
                or status in circuit_codes
                or (
                    banned
                    and status is not None
                    and status in config.get("BLOCK_CODES", ())
                )
            )
            if not trips:
                return False

            now = time.monotonic()
            if slot.cooldown_until and now < slot.cooldown_until:
                return False

            slot.consecutive_failures += 1
            if slot.consecutive_failures < threshold:
                return False

            slot.cooldown_until = time.monotonic() + cooldown_s
            slot.consecutive_failures = 0
            host = proxy_host_for_stats(proxy) or proxy
            reason = "connection failure(s)" if connection_failed else "block(s)"
            console.warning(
                f"Proxy {host!r} cooling down for {domain!r} "
                f"({cooldown_s:.0f}s) after {threshold} {reason}"
            )
            return True

    def pick(
        self,
        proxies: list[str],
        *,
        domain: str | None = None,
        exclude: str | None = None,
    ) -> str | None:
        if not proxies:
            return None
        if not config.get("STEALTH_PROXY_HEALTH"):
            pool = [p for p in proxies if p != exclude] or list(proxies)
            return random.choice(pool)

        candidates = [p for p in proxies if p != exclude] or list(proxies)
        available = [p for p in candidates if self.is_available(p, domain)]
        pool = available or candidates
        best_score = max(self.score(p, domain) for p in pool)
        top = [p for p in pool if self.score(p, domain) == best_score]
        return random.choice(top)


_registry = ProxyHealthRegistry()


def get_proxy_health_registry() -> ProxyHealthRegistry:
    return _registry
