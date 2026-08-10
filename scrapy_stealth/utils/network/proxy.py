from __future__ import annotations

import random
from urllib.parse import urlparse

_VALID_SCHEMES = {"http", "https", "socks4", "socks5"}


def validate_proxies(proxies: list[str]) -> list[str]:
    valid: list[str] = []
    for proxy in proxies:
        try:
            parsed = urlparse(proxy)
            if parsed.scheme not in _VALID_SCHEMES:
                raise ValueError(f"unsupported scheme {parsed.scheme!r}")
            if not parsed.hostname:
                raise ValueError("missing host")
            if not parsed.port:
                raise ValueError("missing port")
        except Exception as exc:
            raise ValueError(f"Invalid proxy {proxy!r}: {exc}") from exc
        valid.append(proxy)
    return valid


def pick(proxies: list[str]) -> str | None:
    if not proxies:
        return None
    return random.choice(proxies)
