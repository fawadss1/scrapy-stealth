from __future__ import annotations

from typing import Any

from .constants import (
    BLOCK_CODES,
    BLOCK_KEYWORDS,
    DEFAULT_ENGINE,
    DEFAULT_PROFILE,
    DEFAULT_TIMEOUT,
    LOGGER_NAME,
)


class StealthConfig:
    """Centralised configuration for scrapy-stealth.

    Modify the shared ``config`` instance before your spider starts::

        from scrapy_stealth.config import config

        config.DEFAULT_PROFILE = "chrome_147"
        config.DEFAULT_TIMEOUT = 30
        config.DEFAULT_ENGINE = "stealth"
        config.BLOCK_CODES |= {403}
        config.BLOCK_KEYWORDS.append("captcha")
    """

    DEFAULT_ENGINE: str = DEFAULT_ENGINE
    DEFAULT_PROFILE: str = DEFAULT_PROFILE
    DEFAULT_TIMEOUT: int = DEFAULT_TIMEOUT
    BLOCK_CODES: frozenset[int] = BLOCK_CODES
    BLOCK_KEYWORDS: list[str] = BLOCK_KEYWORDS
    LOGGER_NAME: str = LOGGER_NAME

    def get(self, key: str, default: Any = None) -> Any:
        """Return a config value by name, with an optional fallback."""
        return getattr(self, key, default)


config = StealthConfig()
