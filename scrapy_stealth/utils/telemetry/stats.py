from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


def proxy_host_for_stats(proxy: str | None) -> str | None:
    """Return ``host:port`` only — never credentials — for Scrapy stats dumps."""
    if not proxy:
        return None
    try:
        parsed = urlparse(proxy)
    except Exception:
        return None
    host = parsed.hostname
    if not host:
        return None
    if parsed.port:
        return f"{host}:{parsed.port}"
    return host


class StealthStats:
    """Thin wrapper around Scrapy's ``StatsCollector`` (no-op if missing)."""

    def __init__(self, stats: Any | None = None) -> None:
        self._stats = stats

    def inc(self, key: str, count: int = 1) -> None:
        if self._stats is None:
            return
        self._stats.inc_value(key, count)

    def set(self, key: str, value: Any) -> None:
        if self._stats is None:
            return
        self._stats.set_value(key, value)

    def set_profile(self, profile: str | None) -> None:
        if profile:
            self.set("stealth/profile", profile)

    def set_proxy(self, proxy: str | None) -> None:
        host = proxy_host_for_stats(proxy)
        if host is not None:
            self.set("stealth/proxy", host)
        else:
            self.set("stealth/proxy", None)

    def record_request(self, driver: str) -> None:
        self.inc("stealth/requests")
        self.inc(f"stealth/requests/{driver}")
        self.set("stealth/driver", driver)

    def record_response(self, driver: str, status: int, banned: bool) -> None:
        """Record one completed response without re-running ban detection."""
        self.inc("stealth/responses")
        self.inc(f"stealth/responses/{driver}")
        self.inc(f"stealth/status/{status}")
        if not banned and status < 400:
            self.inc("stealth/successes")
            self.inc(f"stealth/successes/{driver}")
        else:
            self.inc("stealth/failures")
            self.inc(f"stealth/failures/{driver}")

    def record_dns(self, driver: str, host_count: int) -> None:
        """Record effective DNS overrides only when at least one host is pinned."""
        self.set("stealth/dns/active_hosts", host_count)
        if host_count <= 0:
            return
        self.inc("stealth/dns/requests")
        self.inc(f"stealth/dns/requests/{driver}")
        self.inc("stealth/dns/hosts", host_count)

    def record_proxy_request(self, driver: str) -> None:
        self.inc("stealth/proxy/requests")
        self.inc(f"stealth/proxy/requests/{driver}")

    def record_ban(self, driver: str, streak: int, banned: bool) -> None:
        if banned:
            self.inc("stealth/bans")
            self.inc(f"stealth/bans/{driver}")
        self.set("stealth/ban_streak", streak)

    def record_recycle(self, driver: str) -> None:
        self.inc("stealth/recycles")
        self.inc(f"stealth/recycles/{driver}")

    def record_fallback(
        self, from_driver: str, to_driver: str, method: str | None = None
    ) -> None:
        self.inc("stealth/fallbacks")
        self.inc(f"stealth/fallbacks/{from_driver}")
        if method:
            self.inc(f"stealth/fallbacks/method/{method.lower()}")
        self.set("stealth/fallback_driver", to_driver)

    def record_browser_cookies(self, count: int) -> None:
        if count <= 0:
            return
        self.inc("stealth/browser_cookies_exported", count)
