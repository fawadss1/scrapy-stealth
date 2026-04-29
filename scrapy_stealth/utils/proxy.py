from __future__ import annotations

import random


def pick(proxies: list[str]) -> str | None:
    if not proxies:
        return None
    return random.choice(proxies)
