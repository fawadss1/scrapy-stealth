from __future__ import annotations

import hashlib
import random
import time


def _profile_seed(profile: str) -> int:
    digest = hashlib.sha256((profile or "default").encode()).digest()
    return int.from_bytes(digest[:4])


def apply_request_timing(profile: str) -> None:
    """Simulate pre-request human pause on HTTP drivers (no DOM available).

    Uses a profile-seeded RNG so consecutive requests from the same fingerprint
    stay in a plausible timing band without identical delays every time.
    """
    rng = random.Random(_profile_seed(profile))
    delay = max(0.03, min(0.35, rng.gauss(0.12, 0.04) + rng.random() * 0.08))
    time.sleep(delay)
