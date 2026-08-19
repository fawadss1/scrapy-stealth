from __future__ import annotations

import contextlib
from http.cookiejar import Cookie
from typing import Any
from urllib.parse import urlparse

from ..network.request import parse_cookie_pairs


def _normalize_expires(expires: Any) -> float | None:
    """CDP uses ``-1`` for session cookies; cookiejar treats that as already expired."""
    if expires is None:
        return None
    try:
        value = float(expires)
    except (TypeError, ValueError):
        return None
    return None if value <= 0 else value


def cdp_cookie_to_dict(cookie: Any) -> dict[str, Any]:
    """Normalize a nodriver CDP ``Cookie`` to plain JSON-friendly fields."""
    expires = _normalize_expires(getattr(cookie, "expires", None))
    return {
        "name": str(getattr(cookie, "name", "") or ""),
        "value": str(getattr(cookie, "value", "") or ""),
        "domain": str(getattr(cookie, "domain", "") or ""),
        "path": str(getattr(cookie, "path", "") or "/"),
        "secure": bool(getattr(cookie, "secure", False)),
        "httpOnly": bool(getattr(cookie, "http_only", False)),
        "session": bool(getattr(cookie, "session", False)),
        "expires": expires,
    }


async def collect_browser_cookies(page: Any, url: str) -> list[dict[str, Any]]:
    """Read cookies visible to the tab for ``url`` (after navigation or fetch)."""
    import nodriver.cdp.network as network

    parsed = urlparse(url)
    urls = [url]
    origin = f"{parsed.scheme}://{parsed.netloc}/"
    if origin not in urls:
        urls.append(origin)

    with contextlib.suppress(Exception):
        raw = await page.send(network.get_cookies(urls=urls))
        if raw:
            return [cdp_cookie_to_dict(item) for item in raw]

    with contextlib.suppress(Exception):
        raw = await page.send(network.get_all_cookies())
        if not raw:
            return []
        host = parsed.hostname or ""
        return [
            cdp_cookie_to_dict(item)
            for item in raw
            if _cookie_matches_url(cdp_cookie_to_dict(item), url, host)
        ]
    return []


def _cookie_matches_url(cookie: dict[str, Any], url: str, host: str) -> bool:
    domain = (cookie.get("domain") or "").lstrip(".")
    if not domain or not host:
        return False
    if host != domain and not host.endswith(f".{domain}"):
        return False
    path = cookie.get("path") or "/"
    parsed = urlparse(url)
    req_path = parsed.path or "/"
    return req_path.startswith(path)


def format_cookie_header(cookies: list[dict[str, Any]]) -> str:
    """Build a ``Cookie`` request header from collected browser cookies."""
    pairs: list[str] = []
    seen: set[str] = set()
    for item in cookies:
        name = item.get("name") or ""
        if not name or name in seen:
            continue
        seen.add(name)
        pairs.append(f"{name}={item.get('value', '')}")
    return "; ".join(pairs)


def merge_cookie_header(existing: str | None, collected: str) -> str:
    """Merge an incoming header with browser cookies (browser wins on name clash)."""
    merged = dict(parse_cookie_pairs(existing or ""))
    merged.update(dict(parse_cookie_pairs(collected)))
    return "; ".join(f"{name}={value}" for name, value in merged.items())


def browser_cookie_to_jar_cookie(item: dict[str, Any], url: str) -> Cookie | None:
    """Build an ``http.cookiejar.Cookie`` from a collected browser cookie dict."""
    name = item.get("name") or ""
    if not name:
        return None
    parsed = urlparse(url)
    host = parsed.hostname or ""
    domain = (item.get("domain") or host or "").lstrip(".")
    path = item.get("path") or "/"
    secure = bool(item.get("secure", False))
    expires = _normalize_expires(item.get("expires"))
    is_session = bool(item.get("session", False)) or expires is None
    expires_int = int(expires) if expires is not None else None
    return Cookie(
        version=0,
        name=name,
        value=str(item.get("value") or ""),
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=bool(domain),
        domain_initial_dot=bool(str(item.get("domain") or "").startswith(".")),
        path=path,
        path_specified=bool(path),
        secure=secure,
        expires=expires_int,
        discard=is_session,
        comment=None,
        comment_url=None,
        rest={"HttpOnly": ""} if item.get("httpOnly") else {},
    )


def merge_browser_cookies_to_jar(
    jar: Any, request: Any, cookies: list[dict[str, Any]]
) -> int:
    """Insert browser cookies into Scrapy's cookie jar for follow-up HTTP requests."""
    if jar is None or not cookies or request is None:
        return 0
    merged = 0
    url = getattr(request, "url", "") or ""
    for item in cookies:
        cookie = browser_cookie_to_jar_cookie(item, url)
        if cookie is None:
            continue
        with contextlib.suppress(Exception):
            jar.set_cookie_if_ok(cookie, request)
            merged += 1
    return merged
