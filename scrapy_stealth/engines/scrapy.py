from .base import BaseEngine


class ScrapyEngine(BaseEngine):
    """Default Scrapy engine (fallback)."""

    def fetch(self, request, spider):
        return None
