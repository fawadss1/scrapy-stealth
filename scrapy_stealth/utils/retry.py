from __future__ import annotations

from scrapy.http import Request

from ..constants import BLOCK_CODES


def is_blocked(response) -> bool:
    return response.status in BLOCK_CODES


def build_retry(request: Request) -> Request:
    meta = request.meta.copy()
    meta["retry_times"] = meta.get("retry_times", 0) + 1
    meta["engine"] = "stealth"
    return request.replace(meta=meta, dont_filter=True)
