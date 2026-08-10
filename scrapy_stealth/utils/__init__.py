"""Shared helpers for scrapy-stealth.

Subpackages
-----------
core
    Request meta, responses, logging, console output.
detection
    Anti-bot and JS-challenge heuristics.
network
    DNS overrides, HTTP headers, proxy pool.
browser
    Chrome/CDP runtime, nodriver patch, session tracking.
engine
    Driver fallback, retries, browser profile resolution.
telemetry
    Scrapy stats and PyPI update checks.

Typical imports::

    from scrapy_stealth.utils import console, StealthStats
    from scrapy_stealth.utils.core.meta import STEALTH_KEY
    from scrapy_stealth.utils.network.proxy import pick

Subpackages are also available lazily::

    from scrapy_stealth.utils import network
"""

from __future__ import annotations

import importlib
from typing import Any

_SUBPACKAGES = frozenset(
    {"browser", "core", "detection", "engine", "network", "telemetry"}
)

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Core
    "Console": (".core.console", "Console"),
    "STEALTH_KEY": (".core.meta", "STEALTH_KEY"),
    "StealthResponse": (".core.response", "StealthResponse"),
    "console": (".core.console", "console"),
    "get_logger": (".core.logger", "get_logger"),
    # Detection
    "is_blocked": (".detection.antibot", "is_blocked"),
    "is_browser_session_ban": (".detection.antibot", "is_browser_session_ban"),
    "is_js_challenge": (".detection.antibot", "is_js_challenge"),
    # Engine
    "FALLBACK_DRIVER": (".engine.fallback", "FALLBACK_DRIVER"),
    "build_retry": (".engine.retry", "build_retry"),
    "mark_fallback_done": (".engine.fallback", "mark_fallback_done"),
    "resolve_browser": (".engine.profiles", "resolve_browser"),
    "resolve_primary_driver": (".engine.fallback", "resolve_primary_driver"),
    "should_driver_fallback": (".engine.fallback", "should_driver_fallback"),
    # Network
    "get_default_headers": (".network.headers", "get_default_headers"),
    "merge_headers": (".network.headers", "merge_headers"),
    "pick": (".network.proxy", "pick"),
    "validate_proxies": (".network.proxy", "validate_proxies"),
    # Telemetry
    "StealthStats": (".telemetry.stats", "StealthStats"),
    "proxy_host_for_stats": (".telemetry.stats", "proxy_host_for_stats"),
    "update_available": (".telemetry.updates", "update_available"),
}

__all__ = sorted(_SUBPACKAGES | _LAZY_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    if name in _SUBPACKAGES:
        return importlib.import_module(f"{__name__}.{name}")
    if name in _LAZY_EXPORTS:
        module_path, attr = _LAZY_EXPORTS[name]
        module = importlib.import_module(module_path, __name__)
        return getattr(module, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
