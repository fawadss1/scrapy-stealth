"""Browser engine helpers (CDP, Chrome launch, proxy relay, session tracking)."""

from __future__ import annotations

from ._core import (
    _BROWSER_ARGS,
    _JS_HTML,
    _JS_IS_CHROME_ERROR,
    ProxyRelay,
    _block_static_assets,
    _cdp_snapshot,
    _cleanup_browser_temp_data,
    _ensure_xvfb,
    _is_browser_crash,
    _make_loop,
    _proxy_bypass_args,
    _random_fingerprint_args,
    _silence_browser,
    _smart_wait,
    _splash_url,
    _start_browser_relay,
    _stop_loop,
    _wait_for_status,
)
from .fingerprints import POOL, WEIGHTS
from .patch import patch_nodriver
from .session import BanStreakTracker, SessionCache

__all__ = [
    "POOL",
    "WEIGHTS",
    "BanStreakTracker",
    "ProxyRelay",
    "SessionCache",
    "_BROWSER_ARGS",
    "_JS_HTML",
    "_JS_IS_CHROME_ERROR",
    "_block_static_assets",
    "_cdp_snapshot",
    "_cleanup_browser_temp_data",
    "_ensure_xvfb",
    "_is_browser_crash",
    "_make_loop",
    "_proxy_bypass_args",
    "_random_fingerprint_args",
    "_silence_browser",
    "_smart_wait",
    "_splash_url",
    "_start_browser_relay",
    "_stop_loop",
    "_wait_for_status",
    "patch_nodriver",
]
