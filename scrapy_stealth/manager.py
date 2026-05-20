from __future__ import annotations

from .config import config
from .constants import STEALTH_DRIVER as _DEFAULT_DRIVER
from .engines.base import BaseEngine
from .engines.basic import BasicEngine
from .engines.browser import BrowserEngine
from .engines.scrapy import ScrapyEngine
from .engines.turbo import TurboEngine
from .utils.logger import get_logger

logger = get_logger()

_STEALTH_DRIVERS: dict[str, type[BaseEngine]] = {
    "basic": BasicEngine,
    "turbo": TurboEngine,
    "browser": BrowserEngine,
}


class EngineManager:
    """Handles engine registration and selection."""

    def __init__(self) -> None:
        self._scrapy = ScrapyEngine()
        self._stealth: dict[str, BaseEngine] = {
            name: cls() for name, cls in _STEALTH_DRIVERS.items()
        }

    def get(self, engine_name: str, driver: str | None = None) -> BaseEngine:
        if engine_name == "stealth":
            resolved = driver or config.get("STEALTH_DRIVER")
            if resolved not in self._stealth:
                default = _DEFAULT_DRIVER
                logger.error(
                    "Unknown driver %r. Available drivers: %s. Falling back to %r.",
                    resolved,
                    ", ".join(f"'{k}'" for k in self._stealth),
                    default,
                )
                return self._stealth[default]
            return self._stealth[resolved]
        return self._scrapy
