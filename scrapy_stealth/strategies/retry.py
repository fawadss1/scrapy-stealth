from __future__ import annotations

from scrapy.http import Request, Response

from ..detectors.antibot import AntiBotDetector
from ..utils.retry import build_retry


class RetryHandler:
    """Detects blocked responses and builds stealth retry requests."""

    @staticmethod
    def should_retry(response: Response) -> bool:
        return AntiBotDetector.is_blocked(response) and not AntiBotDetector.is_js_challenge(response)

    @staticmethod
    def build(request: Request) -> Request:
        return build_retry(request)
