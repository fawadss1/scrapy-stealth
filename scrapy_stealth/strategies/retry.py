from __future__ import annotations

from scrapy.http import Request, Response

from ..utils.retry import build_retry, is_blocked


class RetryHandler:
    """Detects blocked responses and builds stealth retry requests."""

    @staticmethod
    def should_retry(response: Response) -> bool:
        return is_blocked(response)

    @staticmethod
    def build(request: Request) -> Request:
        return build_retry(request)
