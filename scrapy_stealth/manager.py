from __future__ import annotations

from .config import config
from .constants import STEALTH_DRIVER as _DEFAULT_DRIVER
from .engines.base import BaseEngine
from .engines.basic import BasicEngine
from .engines.browser import BrowserEngine
from .engines.scrapy import ScrapyEngine
from .engines.turbo import TurboEngine
from .utils.console import console

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
                console.warning(
                    f"Unknown driver {resolved!r}. Available drivers: "
                    f"{', '.join(repr(k) for k in self._stealth)}. Falling back to {default!r}."
                )
                return self._stealth[default]
            return self._stealth[resolved]
        return self._scrapy
