import time
from unittest.mock import MagicMock

import pytest

from scrapy_stealth.behaviors.timing import profile_request_delay
from scrapy_stealth.strategies.throttle import (
    ThrottleRegistry,
    get_throttle_registry,
    parse_retry_after,
)
from scrapy_stealth.utils.telemetry.stats import StealthStats


class TestParseRetryAfter:
    def test_integer_seconds(self):
        assert parse_retry_after("60") == 60.0
        assert parse_retry_after(b"10") == 10.0

    def test_invalid_returns_none(self):
        assert parse_retry_after("") is None
        assert parse_retry_after("not-a-date") is None


class TestProfileRequestDelay:
    def test_within_band(self):
        delay = profile_request_delay("chrome150")
        assert 0.03 <= delay <= 0.43


class TestThrottleRegistry:
    def test_wait_applies_profile_jitter(self, monkeypatch):
        registry = ThrottleRegistry()
        slept: list[float] = []

        monkeypatch.setattr(
            "scrapy_stealth.strategies.throttle.profile_request_delay",
            lambda _profile: 0.15,
        )
        monkeypatch.setattr(
            "scrapy_stealth.strategies.throttle.time.sleep", slept.append
        )

        waited = registry.wait("example.com", "turbo", profile="chrome150")
        assert waited == pytest.approx(0.15)
        assert slept == [0.15]

    def test_429_multiplies_delay(self, monkeypatch):
        registry = ThrottleRegistry()
        monkeypatch.setattr(
            "scrapy_stealth.strategies.throttle.time.sleep", lambda _: None
        )

        registry.record(
            "example.com",
            "turbo",
            status=429,
            latency_s=0.2,
            headers={"Retry-After": "5"},
        )
        slot = registry._slot("example.com", "turbo")
        assert slot.delay >= 1.0
        assert slot.rate_limit_until > time.monotonic()

    def test_success_streak_decreases_delay(self, monkeypatch):
        registry = ThrottleRegistry()
        monkeypatch.setattr(
            "scrapy_stealth.strategies.throttle.time.sleep", lambda _: None
        )

        slot = registry._slot("example.com", "basic")
        slot.delay = 0.5
        for _ in range(4):
            registry.record(
                "example.com",
                "basic",
                status=200,
                latency_s=0.1,
            )
        assert slot.delay == pytest.approx(0.46)

    def test_stats_on_wait_and_429(self, monkeypatch):
        registry = ThrottleRegistry()
        collector = MagicMock()
        values: dict[str, int] = {}

        def inc_value(key: str, count: int = 1) -> None:
            values[key] = values.get(key, 0) + count

        collector.inc_value.side_effect = inc_value
        stats = StealthStats(collector)

        monkeypatch.setattr(
            "scrapy_stealth.strategies.throttle.profile_request_delay",
            lambda _profile: 0.2,
        )
        monkeypatch.setattr(
            "scrapy_stealth.strategies.throttle.time.sleep", lambda _: None
        )

        registry.wait("example.com", "turbo", profile="chrome150", stats=stats)
        registry.record(
            "example.com",
            "turbo",
            status=429,
            latency_s=0.3,
            headers={"Retry-After": "30"},
            stats=stats,
        )

        assert values.get("stealth/throttle/waits") == 1
        assert values.get("stealth/throttle/rate_limited") == 1
        assert values.get("stealth/throttle/retry_after") == 1

    def test_reset_clears_state(self):
        registry = ThrottleRegistry()
        registry._slot("example.com", "turbo").delay = 2.0
        registry.reset()
        assert registry._slots == {}

    def test_singleton(self):
        assert get_throttle_registry() is get_throttle_registry()
