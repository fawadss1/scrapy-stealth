from __future__ import annotations

from .config import config
from .engines.base import BaseEngine
from .engines.browser import BrowserEngine
from .engines.scrapy import ScrapyEngine


class EngineManager:
    """Handles engine registration and selection."""

    def __init__(self) -> None:
        self._engines: dict[str, BaseEngine] = {
            config.get("DEFAULT_ENGINE"): ScrapyEngine(),
            "stealth": BrowserEngine(),
        }

    def get(self, name: str) -> BaseEngine:
        return self._engines.get(name, self._engines[config.get("DEFAULT_ENGINE")])
