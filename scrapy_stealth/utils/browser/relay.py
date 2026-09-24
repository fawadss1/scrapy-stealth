from __future__ import annotations

import socket
import sys
from urllib.parse import quote, urlparse

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def is_loopback_host(host: str) -> bool:
    return host.strip().lower().strip("[]") in _LOOPBACK_HOSTS


def _detect_outbound_ip() -> str | None:
    """Best-effort LAN IP of the machine running Scrapy (for CDP browser reachability)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
        finally:
            sock.close()
    except OSError:
        return None


def resolve_browser_relay_advertise_host(*, external_cdp: bool = False) -> str:
    """Host/IP the browser uses in ``--proxy-server`` / CDP ``proxyServer``."""
    if not external_cdp:
        return "127.0.0.1"
    if ip := _detect_outbound_ip():
        return ip
    return "172.17.0.1" if sys.platform != "win32" else "127.0.0.1"


def resolve_browser_relay_bind_host(
    advertise_host: str | None = None, *, external_cdp: bool = False
) -> str:
    """Local address the CONNECT relay listens on (``asyncio.start_server``)."""
    if external_cdp:
        return "0.0.0.0"
    host = advertise_host or resolve_browser_relay_advertise_host()
    if not is_loopback_host(host):
        return "0.0.0.0"
    return "127.0.0.1"


def format_relay_proxy_server(port: int, host: str | None = None) -> str:
    """Build ``http://host:port`` for Chrome / CDP proxy settings."""
    advertise = host or resolve_browser_relay_advertise_host()
    if ":" in advertise and not advertise.startswith("["):
        return f"http://[{advertise}]:{port}"
    return f"http://{advertise}:{port}"


def chromium_proxy_server_from_url(proxy_url: str) -> str:
    """CDP ``proxyServer`` value for an upstream HTTP(S) proxy (credentials embedded)."""
    parsed = urlparse(proxy_url if "://" in proxy_url else f"http://{proxy_url}")
    host = parsed.hostname
    if not host:
        raise ValueError(f"Invalid proxy URL: {proxy_url!r}")
    port = parsed.port or (443 if parsed.scheme == "https" else 8080)
    if parsed.username:
        user = quote(parsed.username, safe="")
        password = quote(parsed.password or "", safe="")
        return f"http://{user}:{password}@{host}:{port}"
    if parsed.scheme == "socks5":
        return f"socks5://{host}:{port}"
    return f"http://{host}:{port}"


def proxy_url_has_credentials(proxy_url: str) -> bool:
    parsed = urlparse(proxy_url if "://" in proxy_url else f"http://{proxy_url}")
    return bool(parsed.username)


def external_cdp_uses_direct_upstream_proxy(
    *, external_cdp: bool, proxy: str | None, dns_overrides: dict[str, str]
) -> bool:
    """Use upstream ``proxyServer`` only for external CDP without DNS pin or proxy auth."""
    if not external_cdp or not proxy or dns_overrides:
        return False
    return not proxy_url_has_credentials(proxy)
