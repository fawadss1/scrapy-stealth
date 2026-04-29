from __future__ import annotations

from .engines.base import BaseEngine
from .engines.browser import BrowserEngine
from .engines.scrapy import ScrapyEngine


class EngineManager:
    """Handles engine registration and selection."""

    def __init__(self) -> None:
        self._engines: dict[str, BaseEngine] = {
            "scrapy": ScrapyEngine(),
            "stealth": BrowserEngine(),
        }

    def get(self, name: str) -> BaseEngine:
        return self._engines.get(name, self._engines["scrapy"])
