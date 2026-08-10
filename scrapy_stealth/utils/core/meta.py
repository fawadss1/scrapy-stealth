from __future__ import annotations

from typing import Any

from scrapy.http import Request

STEALTH_KEY = "stealth"


def _stealth_meta(request: Request) -> dict:
    val = request.meta.get(STEALTH_KEY, {})
    return val if isinstance(val, dict) else {}


def _resolve_engine(request: Request, default: str) -> str:
    return "stealth" if isinstance(request.meta.get(STEALTH_KEY), dict) else default


def _get_meta_data(request: Request, key: str, default: Any = None) -> Any:
    return _stealth_meta(request).get(key, default)
