from __future__ import annotations

import random

from .noise import gaussian, jitter_point
from .viewport import ViewportSpec


def _bezier(
    start: tuple[float, float],
    end: tuple[float, float],
    steps: int,
) -> list[tuple[float, float]]:
    """Quadratic-bezier mouse path with a random control point."""
    sx, sy = start
    ex, ey = end
    cx = gaussian((sx + ex) / 2, abs(ex - sx) * 0.15)
    cy = gaussian((sy + ey) / 2, abs(ey - sy) * 0.15)
    points: list[tuple[float, float]] = []
    for i in range(1, steps + 1):
        t = i / steps
        inv = 1 - t
        x = inv * inv * sx + 2 * inv * t * cx + t * t * ex
        y = inv * inv * sy + 2 * inv * t * cy + t * t * ey
        points.append(jitter_point(x, y))
    return points


def landing_interactions(
    spec: ViewportSpec,
) -> tuple[list[tuple[float, float]], list[int]]:
    """Build a mouse path and scroll deltas for a typical landing-page visit."""
    width = float(spec.width)
    height = float(spec.height)
    start = (
        gaussian(width * 0.2, width * 0.05, low=8.0, high=width - 8.0),
        gaussian(height * 0.15, height * 0.05, low=8.0, high=height - 8.0),
    )
    end = (
        gaussian(width * 0.55, width * 0.08, low=8.0, high=width - 8.0),
        gaussian(height * 0.45, height * 0.08, low=8.0, high=height - 8.0),
    )
    steps = random.randint(8, 14)
    mouse_path = _bezier(start, end, steps)

    scroll_count = random.randint(2, 4)
    scrolls = [
        int(gaussian(220, 60, low=80, high=min(480, int(height * 0.6))))
        for _ in range(scroll_count)
    ]
    return mouse_path, scrolls


def step_delay_s(*, mobile: bool) -> float:
    """Pause between interaction steps (seconds)."""
    mean = 0.055 if mobile else 0.04
    return gaussian(mean, 0.015, low=0.015, high=0.12)
