from __future__ import annotations

from typing import Any

from scrapy.http import Request

STEALTH_KEY = "stealth"


def _stealth_meta(request: Request) -> dict:
    return request.meta.get(STEALTH_KEY, {})


def _resolve_engine(request: Request, default: str) -> str:
    return "stealth" if STEALTH_KEY in request.meta else default


def _is_meta_enabled(request: Request, key: str) -> bool:
    return bool(_stealth_meta(request).get(key))


def _get_meta_data(request: Request, key: str, default: Any = None) -> Any:
    return _stealth_meta(request).get(key, default)
