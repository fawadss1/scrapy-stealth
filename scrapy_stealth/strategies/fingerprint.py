from __future__ import annotations

import random

from ..utils.fingerprints import POOL, WEIGHTS

FINGERPRINTS: list[str] = POOL


class ProfileRotator:
    """Rotate browser fingerprints."""

    @staticmethod
    def get() -> str:
        return random.choices(POOL, weights=WEIGHTS)[0]
