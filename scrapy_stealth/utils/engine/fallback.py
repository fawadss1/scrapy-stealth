from __future__ import annotations

from scrapy.http import Request, Response

from ...config import config
from ..core.meta import STEALTH_KEY, _get_meta_data, _stealth_meta
from ..detection.antibot import is_browser_session_ban, is_js_challenge

_HTTP_DRIVERS = frozenset({"basic", "turbo"})
FALLBACK_DRIVER = "browser"
FALLBACK_DONE_KEY = "_driver_fallback_done"


def resolve_primary_driver(driver: str | None) -> str | None:
    """Expand ``driver="auto"`` to the HTTP primary driver; pass other values through."""
    requested = driver if driver is not None else config.get("STEALTH_DRIVER")
    if requested != "auto":
        return driver
    configured = config.get("STEALTH_DRIVER")
    if configured in _HTTP_DRIVERS:
        return configured
    return "turbo"


def should_driver_fallback(
    response: Response,
    primary_driver: str,
    request: Request,
) -> bool:
    """True when this response should be retried once with the fallback driver."""
    meta = _stealth_meta(request)
    if meta.get(FALLBACK_DONE_KEY):
        return False
    if meta.get("fallback") is False:
        return False

    if _get_meta_data(request, "driver") != "auto":
        return False
    if primary_driver not in _HTTP_DRIVERS:
        return False

    try:
        body = response.text
    except Exception:
        return is_browser_session_ban(response)
    return is_js_challenge(body) or is_browser_session_ban(response)


def mark_fallback_done(request: Request, primary_driver: str) -> None:
    """Record fallback state and force visible Chrome for the browser retry."""
    stealth = request.meta.get(STEALTH_KEY)
    if not isinstance(stealth, dict):
        stealth = {}
        request.meta[STEALTH_KEY] = stealth
    stealth[FALLBACK_DONE_KEY] = True
    stealth["fallback_from"] = primary_driver
    stealth["headless"] = False
