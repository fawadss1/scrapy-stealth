from __future__ import annotations

from typing import Any, Final

from .constants import (
    BLOCK_CODES,
    BLOCK_KEYWORDS,
    BROWSER_CHALLENGE_TIMEOUT_S,
    BROWSER_EXECUTABLE_PATH,
    BROWSER_EXPORT_COOKIES,
    BROWSER_HEADLESS,
    BROWSER_MAX_TABS,
    BROWSER_NO_SANDBOX,
    BROWSER_PROXY_BYPASS_LIST,
    BROWSER_SETTLE_S,
    BROWSER_STATIC_ASSETS_BLOCK,
    DEFAULT_ENGINE,
    DEFAULT_TIMEOUT,
    HTTP2,
    HTTP3,
    LOGGER_NAME,
    STEALTH_DNS_OVERRIDES,
    STEALTH_DRIVER,
    STEALTH_ENABLED,
    STEALTH_PROXIES,
    STEALTH_RECYCLE_AFTER_BANS,
    STEALTH_RECYCLE_COOLDOWN_S,
)


class StealthConfig:
    """Centralised configuration for scrapy-stealth.

    Modify the shared ``config`` instance before your spider starts::

        from scrapy_stealth.config import config

        config.DEFAULT_ENGINE = "stealth"
        config.DEFAULT_TIMEOUT = 30
        config.STEALTH_DRIVER = "turbo"
        config.STEALTH_DNS_OVERRIDES = {"example.com": "203.0.113.10"}
        config.BLOCK_CODES |= {403}
        config.BLOCK_KEYWORDS.append("captcha")
    """

    DEFAULT_ENGINE: str = DEFAULT_ENGINE
    DEFAULT_TIMEOUT: int = DEFAULT_TIMEOUT
    BLOCK_CODES: frozenset[int] = BLOCK_CODES
    BLOCK_KEYWORDS: list[str] = BLOCK_KEYWORDS
    LOGGER_NAME: Final[str] = LOGGER_NAME
    HTTP2: bool = HTTP2
    HTTP3: bool = HTTP3
    STEALTH_DRIVER: str = STEALTH_DRIVER
    STEALTH_ENABLED: bool = STEALTH_ENABLED
    STEALTH_PROXIES: list[str] = list(STEALTH_PROXIES)
    STEALTH_DNS_OVERRIDES: dict[str, str] = dict(STEALTH_DNS_OVERRIDES)
    BROWSER_HEADLESS: bool = BROWSER_HEADLESS
    BROWSER_SETTLE_S: float = BROWSER_SETTLE_S
    BROWSER_CHALLENGE_TIMEOUT_S: float = BROWSER_CHALLENGE_TIMEOUT_S
    BROWSER_MAX_TABS: int = BROWSER_MAX_TABS
    STEALTH_RECYCLE_AFTER_BANS: int = STEALTH_RECYCLE_AFTER_BANS
    STEALTH_RECYCLE_COOLDOWN_S: float = STEALTH_RECYCLE_COOLDOWN_S
    BROWSER_STATIC_ASSETS_BLOCK: bool = BROWSER_STATIC_ASSETS_BLOCK
    BROWSER_PROXY_BYPASS_LIST: list[str] = BROWSER_PROXY_BYPASS_LIST
    BROWSER_NO_SANDBOX: bool | None = BROWSER_NO_SANDBOX
    BROWSER_EXECUTABLE_PATH: str | None = BROWSER_EXECUTABLE_PATH
    BROWSER_EXPORT_COOKIES: bool = BROWSER_EXPORT_COOKIES

    def get(self, key: str, default: Any = None) -> Any:
        """Return a config value by name, with an optional fallback."""
        return getattr(self, key, default)


config = StealthConfig()
