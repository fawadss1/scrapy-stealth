from __future__ import annotations

from typing import Any, Final

from .constants import (
    BLOCK_CODES,
    BLOCK_KEYWORDS,
    BROWSER_EXECUTABLE_PATH,
    BROWSER_HEADLESS,
    BROWSER_MAX_TABS,
    BROWSER_NO_SANDBOX,
    BROWSER_PROXY_BYPASS_LIST,
    BROWSER_RESTART_AFTER_BANS,
    BROWSER_RESTART_COOLDOWN_S,
    BROWSER_SETTLE_S,
    BROWSER_STATIC_ASSETS_BLOCK,
    DEFAULT_ENGINE,
    DEFAULT_PROFILE,
    DEFAULT_TIMEOUT,
    HTTP2,
    LOGGER_NAME,
    STEALTH_DRIVER,
    STEALTH_ENABLED,
)


class StealthConfig:
    """Centralised configuration for scrapy-stealth.

    Modify the shared ``config`` instance before your spider starts::

        from scrapy_stealth.config import config

        config.DEFAULT_PROFILE = "chrome_147"
        config.DEFAULT_TIMEOUT = 30
        config.DEFAULT_ENGINE = "stealth"
        config.STEALTH_DRIVER = "turbo"
        config.BLOCK_CODES |= {403}
        config.BLOCK_KEYWORDS.append("captcha")
    """

    DEFAULT_ENGINE: str = DEFAULT_ENGINE
    DEFAULT_PROFILE: str = DEFAULT_PROFILE
    DEFAULT_TIMEOUT: int = DEFAULT_TIMEOUT
    BLOCK_CODES: frozenset[int] = BLOCK_CODES
    BLOCK_KEYWORDS: list[str] = BLOCK_KEYWORDS
    LOGGER_NAME: Final[str] = LOGGER_NAME
    HTTP2: bool = HTTP2
    STEALTH_DRIVER: str = STEALTH_DRIVER
    STEALTH_ENABLED: bool = STEALTH_ENABLED
    BROWSER_HEADLESS: bool = BROWSER_HEADLESS
    BROWSER_SETTLE_S: float = BROWSER_SETTLE_S
    BROWSER_MAX_TABS: int = BROWSER_MAX_TABS
    BROWSER_RESTART_AFTER_BANS: int = BROWSER_RESTART_AFTER_BANS
    BROWSER_RESTART_COOLDOWN_S: float = BROWSER_RESTART_COOLDOWN_S
    BROWSER_STATIC_ASSETS_BLOCK: bool = BROWSER_STATIC_ASSETS_BLOCK
    BROWSER_PROXY_BYPASS_LIST: list[str] = BROWSER_PROXY_BYPASS_LIST
    BROWSER_NO_SANDBOX: bool | None = BROWSER_NO_SANDBOX
    BROWSER_EXECUTABLE_PATH: str | None = BROWSER_EXECUTABLE_PATH

    def get(self, key: str, default: Any = None) -> Any:
        """Return a config value by name, with an optional fallback."""
        return getattr(self, key, default)


config = StealthConfig()
