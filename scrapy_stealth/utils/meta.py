from __future__ import annotations

from typing import Any

from scrapy.http import Request


def _is_meta_enabled(request: Request, key: str) -> bool:
    return bool(request.meta.get(key))


def _get_meta_data(request: Request, key: str, default: Any = None) -> Any:
    return request.meta.get(key, default)
