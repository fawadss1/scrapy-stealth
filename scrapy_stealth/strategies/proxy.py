from __future__ import annotations

from ..utils.proxy import pick, validate_proxies


class ProxyRotator:
    """Proxy rotation with validation."""

    def __init__(self, proxies: list[str] | None = None):
        self.proxies = validate_proxies(proxies) if proxies else []

    def get(self) -> str | None:
        return pick(self.proxies)
