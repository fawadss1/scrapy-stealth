from __future__ import annotations

from .config import config
from .engines.base import BaseEngine
from .engines.basic import BasicEngine
from .engines.browser import BrowserEngine
from .engines.scrapy import ScrapyEngine
from .engines.turbo import TurboEngine

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
            return self._stealth.get(resolved, self._stealth["basic"])
        return self._scrapy
