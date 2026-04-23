from __future__ import annotations

import logging
from typing import Any

from scrapy.http import Request

_STEALTH_ONLY_KEYS = ("impersonate", "rotate_profile", "rotate_proxy")


def _is_meta_enabled(request: Request, key: str) -> bool:
    return bool(request.meta.get(key))


def _get_meta_data(request: Request, key: str, default: Any = None) -> Any:
    return request.meta.get(key, default)


def _stealth_ignored_warn(
        request: Request,
        engine_name: str,
        logger: logging.Logger,
) -> bool:
    if engine_name == "stealth":
        return False
    ignored = [k for k in _STEALTH_ONLY_KEYS if _is_meta_enabled(request, k)]
    if ignored:
        logger.warning(
            "Meta keys %s have no effect when engine is %r. "
            "Set meta={'engine': 'stealth'} to use them.",
            ignored,
            engine_name,
        )
        return True
    return False
