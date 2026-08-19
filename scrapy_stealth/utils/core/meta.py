from __future__ import annotations

from typing import Any

from scrapy.http import Request

from ...config import config

STEALTH_KEY = "stealth"


def _stealth_meta(request: Request) -> dict:
    val = request.meta.get(STEALTH_KEY, {})
    return val if isinstance(val, dict) else {}


def _resolve_engine(request: Request, default: str) -> str:
    return "stealth" if isinstance(request.meta.get(STEALTH_KEY), dict) else default


def _get_meta_data(request: Request, key: str, default: Any = None) -> Any:
    return _stealth_meta(request).get(key, default)


def resolve_browser_headless(request: Request) -> bool:
    """Browser runs visible by default; per-request meta or config can opt into headless."""
    stealth = _stealth_meta(request)
    if "headless" in stealth:
        return bool(stealth["headless"])
    return bool(config.get("BROWSER_HEADLESS"))


def apply_browser_driver_defaults(request: Request) -> None:
    """Ensure explicit ``driver="browser"`` requests default to a visible window."""
    stealth = _stealth_meta(request)
    if stealth.get("driver") != "browser":
        return
    stealth.setdefault("headless", False)


def _apply_stealth_enabled_defaults(request: Request, stealth_enabled: bool) -> None:
    """When global stealth is on, use smart driver selection (HTTP first, browser on ban)."""
    if not stealth_enabled:
        return
    stealth = request.meta.get(STEALTH_KEY)
    if stealth is False:
        return
    if STEALTH_KEY not in request.meta or not isinstance(stealth, dict):
        request.meta[STEALTH_KEY] = {"driver": "auto"}
        return
    if "driver" not in stealth:
        stealth["driver"] = "auto"
