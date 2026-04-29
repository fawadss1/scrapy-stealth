from __future__ import annotations

from ..config import config


def is_blocked(response) -> bool:
    if response.status in config.get("BLOCK_CODES"):
        return True
    body = response.text.lower()
    return any(kw in body for kw in config.get("BLOCK_KEYWORDS"))
