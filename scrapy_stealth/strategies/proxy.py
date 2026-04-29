from __future__ import annotations

from ..utils.proxy import pick


class ProxyRotator:
    """Simple proxy rotation strategy."""

    def __init__(self, proxies: list[str] | None = None):
        self.proxies = proxies or []

    def get(self) -> str | None:
        return pick(self.proxies)
