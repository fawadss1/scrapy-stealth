from __future__ import annotations

from .config import config
from .engines.base import BaseEngine
from .engines.scrapy import ScrapyEngine
from .utils.core.console import console
from .utils.engine.fallback import resolve_primary_driver

STEALTH_DRIVER_NAMES: tuple[str, ...] = ("basic", "turbo", "browser")


def _stealth_driver_class(name: str) -> type[BaseEngine]:
    if name == "basic":
        from .engines.basic import BasicEngine

        return BasicEngine
    if name == "turbo":
        from .engines.turbo import TurboEngine

        return TurboEngine
    if name == "browser":
        from .engines.browser import BrowserEngine

        return BrowserEngine
    raise KeyError(name)


class EngineManager:
    """Handles engine registration and selection."""

    def __init__(self) -> None:
        self._scrapy = ScrapyEngine()
        self._stealth: dict[str, BaseEngine] = {}

    def _ensure_stealth(self, name: str) -> BaseEngine:
        if name not in self._stealth:
            self._stealth[name] = _stealth_driver_class(name)()
        return self._stealth[name]

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
                resolved = "turbo"
            if resolved in STEALTH_DRIVER_NAMES:
                return self._ensure_stealth(resolved)
            fallback = config.get("STEALTH_DRIVER") or "turbo"
            default = fallback if fallback in STEALTH_DRIVER_NAMES else "turbo"
            console.warning(
                f"Unknown driver {resolved!r}. Available drivers: "
                f"{', '.join(repr(k) for k in STEALTH_DRIVER_NAMES)}. "
                f"Falling back to {default!r}."
            )
            return self._ensure_stealth(default)
        return self._scrapy
