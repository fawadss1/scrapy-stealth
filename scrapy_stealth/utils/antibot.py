from __future__ import annotations

from ..constants import BLOCK_CODES, BLOCK_KEYWORDS


def is_blocked(response) -> bool:
    if response.status in BLOCK_CODES:
        return True
    body = response.text.lower()
    return any(kw in body for kw in BLOCK_KEYWORDS)
