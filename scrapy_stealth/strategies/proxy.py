from __future__ import annotations

from ..utils.network.proxy import validate_proxies
from .proxy_health import ProxyHealthRegistry, get_proxy_health_registry


class ProxyRotator:
    """Proxy rotation with validation and optional health-aware selection."""

    def __init__(
        self,
        proxies: list[str] | None = None,
        *,
        health: ProxyHealthRegistry | None = None,
    ):
        self.proxies = validate_proxies(proxies) if proxies else []
        self._health = health or get_proxy_health_registry()

    def get(
        self,
        *,
        domain: str | None = None,
        exclude: str | None = None,
    ) -> str | None:
        return self._health.pick(self.proxies, domain=domain, exclude=exclude)
