from __future__ import annotations

import ipaddress
from typing import Any, Mapping
from urllib.parse import urlparse

from scrapy.http import Request

from ...config import config
from ..core.meta import _get_meta_data

DnsOverrides = dict[str, str]


def validate_dns_overrides(overrides: Mapping[str, Any] | None) -> DnsOverrides:
    """
    Validate and normalize a host→IP mapping.

    Raises ``ValueError`` immediately on empty hosts, blank IPs, or addresses
    that are not valid IPv4/IPv6 (same fail-fast style as ``validate_proxies``).
    """
    if not overrides:
        return {}

    valid: DnsOverrides = {}
    for host, ip in overrides.items():
        hostname = str(host).strip().lower().rstrip(".")
        if not hostname:
            raise ValueError(f"Invalid DNS override host {host!r}: empty hostname")
        if "://" in hostname or "/" in hostname:
            raise ValueError(
                f"Invalid DNS override host {host!r}: use a bare hostname "
                f"(e.g. 'example.com'), not a URL"
            )
        address = str(ip).strip()
        if not address:
            raise ValueError(f"Invalid DNS override for {hostname!r}: empty IP")
        try:
            ipaddress.ip_address(address)
        except ValueError as exc:
            raise ValueError(
                f"Invalid DNS override for {hostname!r}: {address!r} is not a "
                f"valid IPv4/IPv6 address"
            ) from exc
        valid[hostname] = address
    return valid


def _normalize_meta_dns(value: Any, request_host: str | None) -> DnsOverrides:
    """Accept a bare IP for this request's host, or a host→IP mapping."""
    if value is None or value is False:
        return {}
    if isinstance(value, str):
        if not request_host:
            raise ValueError(
                "meta['stealth']['dns'] as a bare IP requires a hostname in the "
                "request URL"
            )
        return validate_dns_overrides({request_host: value})
    if isinstance(value, Mapping):
        return validate_dns_overrides(value)
    raise ValueError(
        f"meta['stealth']['dns'] must be an IP string or a {{host: ip}} mapping, "
        f"got {type(value).__name__}"
    )


def resolve_dns_overrides(request: Request) -> DnsOverrides:
    """
    Merge global ``config.STEALTH_DNS_OVERRIDES`` with per-request overrides.

    Per-request values win on hostname collision. Request meta accepts either::

        meta={"stealth": {"dns": "203.0.113.10"}}
        meta={"stealth": {"dns": {"example.com": "203.0.113.10"}}}
    """
    merged = dict(validate_dns_overrides(config.get("STEALTH_DNS_OVERRIDES") or {}))
    hostname = urlparse(request.url).hostname
    if hostname:
        hostname = hostname.lower().rstrip(".")
    meta_dns = _get_meta_data(request, "dns")
    if meta_dns is not None:
        merged.update(_normalize_meta_dns(meta_dns, hostname))
    return merged


def lookup_dns_ip(hostname: str | None, overrides: DnsOverrides) -> str | None:
    """Return the override IP for *hostname*, or ``None`` if unset."""
    if not hostname or not overrides:
        return None
    return overrides.get(hostname.lower().rstrip("."))


def dns_fingerprint(overrides: DnsOverrides) -> tuple[tuple[str, str], ...]:
    """Stable cache/launch key for a host→IP map."""
    return tuple(sorted(overrides.items()))


def default_port_for_url(url: str) -> int:
    parsed = urlparse(url)
    if parsed.port:
        return parsed.port
    return 443 if (parsed.scheme or "https").lower() == "https" else 80


def build_curl_resolve(overrides: DnsOverrides, url: str) -> list[str]:
    """
    Build libcurl ``CURLOPT_RESOLVE`` entries (``host:port:ip``).

    Also emits a same-IP entry for the request host's explicit port when the
    URL uses a non-default port not already covered by an override host.
    """
    if not overrides:
        return []

    port = default_port_for_url(url)
    entries: list[str] = []
    seen: set[str] = set()
    for host, ip in overrides.items():
        entry = f"{host}:{port}:{ip}"
        if entry not in seen:
            entries.append(entry)
            seen.add(entry)
        # Always include both common HTTP ports so redirects stay pinned.
        for extra_port in (80, 443):
            if extra_port == port:
                continue
            extra = f"{host}:{extra_port}:{ip}"
            if extra not in seen:
                entries.append(extra)
                seen.add(extra)
    return entries


def _wreq_dns_options_cls() -> Any:
    """Return wreq's ``DnsOptions`` class from the native extension.

    Resolved via ``getattr`` because the Python ``wreq/dns.py`` stub is
    shadowed by the extension module at runtime, so static analyzers cannot
    see the symbol on a normal import.
    """
    import wreq

    for owner in (wreq, getattr(wreq, "dns", None)):
        if owner is None:
            continue
        cls = getattr(owner, "DnsOptions", None)
        if cls is not None:
            return cls
    raise AttributeError("wreq.DnsOptions is unavailable; upgrade wreq to >= 0.12.1")


def build_wreq_dns_options(overrides: DnsOverrides) -> Any | None:
    """Return a wreq ``DnsOptions`` with custom resolves, or ``None`` if empty."""
    if not overrides:
        return None

    opts = _wreq_dns_options_cls()()
    for host, ip in overrides.items():
        opts.add_resolve(host, [ipaddress.ip_address(ip)])
    return opts


def build_chrome_host_resolver_args(overrides: DnsOverrides) -> list[str]:
    """
    Build Chrome ``--host-resolver-rules`` launch args from a host→IP map.

    Format: ``MAP host ip, MAP host2 ip2``. Returns ``[]`` when empty so
    callers can splat unconditionally. Passed as a single argv element (nodriver
    uses ``create_subprocess_exec``), so spaces inside the rules stay intact.
    """
    if not overrides:
        return []
    rules = ", ".join(f"MAP {host} {ip}" for host, ip in overrides.items())
    return [f"--host-resolver-rules={rules}"]
