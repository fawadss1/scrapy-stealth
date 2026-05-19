from __future__ import annotations

from scrapy.http import Request, Response

from .base import BaseEngine


class ScrapyEngine(BaseEngine):
    """Default Scrapy engine (fallback — delegates to Scrapy's built-in downloader)."""

    async def fetch(self, request, spider):
        return None

    def _execute(self, request: Request) -> Response | None:
        return None
