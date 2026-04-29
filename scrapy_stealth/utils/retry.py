from __future__ import annotations

from scrapy.http import Request

from ..config import config


def is_blocked(response) -> bool:
    return response.status in config.get("BLOCK_CODES")


def build_retry(request: Request) -> Request:
    meta = request.meta.copy()
    meta["retry_times"] = meta.get("retry_times", 0) + 1
    meta["engine"] = "stealth"
    return request.replace(meta=meta, dont_filter=True)
