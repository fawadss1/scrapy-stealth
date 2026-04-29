from __future__ import annotations

import logging
from typing import Any

from scrapy.http import Request, Response
from twisted.internet.defer import Deferred

from ..manager import EngineManager

logger = logging.getLogger(__name__)


class StealthDownloaderMiddleware:
    """Main middleware routing requests through stealth engines."""

    def __init__(self) -> None:
        self.manager = EngineManager()

    @classmethod
    def from_crawler(cls, crawler: Any) -> StealthDownloaderMiddleware:
        return cls()

    def process_request(self, request: Request, spider: Any) -> Response | Deferred | None:
        engine_name = request.meta.get("engine", "scrapy")
        engine = self.manager.get(engine_name)
        return engine.fetch(request, spider)
