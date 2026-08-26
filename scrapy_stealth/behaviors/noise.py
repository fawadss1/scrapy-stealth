from __future__ import annotations

import random


def gaussian(
    mean: float,
    sigma: float,
    *,
    low: float | None = None,
    high: float | None = None,
) -> float:
    value = random.gauss(mean, sigma)
    if low is not None:
        value = max(low, value)
    if high is not None:
        value = min(high, value)
    return value


def jitter_point(x: float, y: float, *, sigma: float = 2.0) -> tuple[float, float]:
    return (
        gaussian(x, sigma, low=0.0),
        gaussian(y, sigma, low=0.0),
    )
