"""Human-like interaction patterns for stealth drivers."""

from .engine import (
    apply_viewport_emulation,
    run_browser_behavior,
    run_browser_interactions,
    simulate_hover,
)
from .timing import apply_request_timing
from .viewport import ViewportSpec, resolve_viewport

__all__ = [
    "ViewportSpec",
    "apply_request_timing",
    "resolve_viewport",
    "apply_viewport_emulation",
    "run_browser_interactions",
    "run_browser_behavior",
    "simulate_hover",
]
