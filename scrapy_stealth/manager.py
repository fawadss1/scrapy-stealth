from __future__ import annotations

from .config import config
from .constants import STEALTH_DRIVER as _DEFAULT_DRIVER
from .engines.base import BaseEngine
from .engines.basic import BasicEngine
from .engines.browser import BrowserEngine
from .engines.scrapy import ScrapyEngine
from .engines.turbo import TurboEngine
from .utils.console import console
from .utils.fallback import resolve_primary_driver

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

    def seed_proxies(self) -> None:
        """Refresh engine default proxies from ``config.STEALTH_PROXIES``."""
        for engine in self._stealth.values():
            engine._default_proxy = None
            engine.seed_proxy_from_config()

    def set_stats(self, stats: object | None) -> None:
        """Attach Scrapy stats collector to all stealth engines."""
        for engine in self._stealth.values():
            engine.set_stats(stats)

    def close(self) -> None:
        for engine in self._stealth.values():
            engine.close()

    def get(self, engine_name: str, driver: str | None = None) -> BaseEngine:
        if engine_name == "stealth":
            resolved = resolve_primary_driver(driver) or config.get("STEALTH_DRIVER")
            if resolved == "auto":
                resolved = "basic"
            if resolved not in self._stealth:
                default = (
                    _DEFAULT_DRIVER if _DEFAULT_DRIVER in self._stealth else "basic"
                )
                console.warning(
                    f"Unknown driver {resolved!r}. Available drivers: "
                    f"{', '.join(repr(k) for k in self._stealth)}. Falling back to {default!r}."
                )
                return self._stealth[default]
            return self._stealth[resolved]
        return self._scrapy
