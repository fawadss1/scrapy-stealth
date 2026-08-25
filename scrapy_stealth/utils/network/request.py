from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scrapy.http import Request

from ...exceptions import StealthRequestError
from .headers import _FINGERPRINT_KEYS, get_default_headers, merge_headers

_SUPPORTED_METHODS = frozenset(
    {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
)
_NAV_METHODS = frozenset({"GET", "HEAD"})
_HOP_BY_HOP_HEADERS = frozenset({"host", "content-length", "cookie"})
_BODY_METHODS = frozenset({"POST", "PUT", "PATCH"})


@dataclass(frozen=True)
class StealthRequestPayload:
    """Validated, normalized request fields for basic, turbo, and browser."""

    url: str
    method: str
    headers: dict[str, str]
    body: bytes | None
    cookie_header: str | None
    extra_headers: dict[str, str]

    @property
    def method_name(self) -> str:
        return self.method.lower()

    @property
    def has_body(self) -> bool:
        return self.body is not None and len(self.body) > 0

    @property
    def needs_browser_setup(self) -> bool:
        """True when browser cannot use a bare CDP create_target(url) navigation."""
        if self.method not in _NAV_METHODS:
            return True
        if self.body is not None:
            return True
        if self.extra_headers or self.cookie_header:
            return True
        return False

    def http_kwargs(self) -> dict[str, Any]:
        """Keyword args shared by basic and turbo HTTP clients."""
        kwargs: dict[str, Any] = {"headers": self.headers}
        if self.body is not None:
            kwargs["data"] = self.body
        return kwargs

    def turbo_kwargs(
        self,
        *,
        timeout: int | float,
        http_version: Any,
        proxy: str | None,
    ) -> dict[str, Any]:
        """curl_cffi kwargs for turbo — cookies via API to preserve impersonate order."""
        headers = dict(self.headers)
        kwargs: dict[str, Any] = {
            "timeout": timeout,
            "http_version": http_version,
            "default_headers": True,
        }
        if self.cookie_header:
            kwargs["cookies"] = dict(parse_cookie_pairs(self.cookie_header))
            headers.pop("Cookie", None)
        if headers:
            kwargs["headers"] = headers
        if self.body is not None:
            kwargs["data"] = self.body
        if proxy:
            kwargs["proxies"] = {"http": proxy, "https": proxy}
        return kwargs

    def basic_http_kwargs(self) -> dict[str, Any]:
        """Keyword args for basic (wreq) — raw bytes via ``body``."""
        kwargs: dict[str, Any] = {"headers": self.headers}
        if self.body is not None:
            kwargs["body"] = self.body
        return kwargs


# Back-compat alias used by browser CDP helpers.
PreparedRequest = StealthRequestPayload


def extract_cookie_header(request: Request) -> str | None:
    raw = request.headers.get("Cookie") or request.headers.get(b"Cookie")
    if raw is None:
        return None
    if isinstance(raw, (bytes, bytearray)):
        return raw.decode("latin-1")
    return str(raw)


def parse_cookie_pairs(cookie_header: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for part in cookie_header.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, _, value = part.partition("=")
        name = name.strip()
        if not name:
            continue
        pairs.append((name, value.strip()))
    return pairs


_parse_cookie_pairs = parse_cookie_pairs


def _extract_extra_headers(request: Request) -> dict[str, str]:
    return {
        k: v
        for k, v in request.headers.to_unicode_dict().items()
        if k.lower() not in (_FINGERPRINT_KEYS | _HOP_BY_HOP_HEADERS)
    }


def _compose_headers(
    extra_headers: dict[str, str],
    cookie_header: str | None,
    profile: str | None,
) -> dict[str, str]:
    if profile:
        headers = merge_headers(get_default_headers(profile), extra_headers)
    else:
        headers = dict(extra_headers)
    if cookie_header:
        headers["Cookie"] = cookie_header
    return headers


def _validate_request(method: str, url: str, body: bytes | None) -> None:
    if not url:
        raise StealthRequestError("Request URL is required")

    if method not in _SUPPORTED_METHODS:
        raise StealthRequestError(
            f"Unsupported HTTP method {method!r} "
            f"(supported: {', '.join(sorted(_SUPPORTED_METHODS))})"
        )

    if method in _BODY_METHODS and body is None:
        # Empty body is valid for POST/PUT/PATCH — no error.
        return

    if method in _NAV_METHODS and body is not None and len(body) > 0:
        # Unusual but allowed; HTTP engines may send it, browser uses setup path.
        return


def build_stealth_request(
    request: Request,
    *,
    profile: str | None = None,
) -> StealthRequestPayload:
    """
    Single entry point for all stealth drivers.

    Normalizes and validates method, URL, body, Cookie, and custom headers;
    strips fingerprint headers (each engine sets its own impersonation layer).
    """
    url = (request.url or "").strip()
    method = (request.method or "GET").upper()
    body = bytes(request.body) if request.body else None

    _validate_request(method, url, body)

    extra_headers = _extract_extra_headers(request)
    cookie_header = extract_cookie_header(request)
    headers = _compose_headers(extra_headers, cookie_header, profile)

    return StealthRequestPayload(
        url=url,
        method=method,
        headers=headers,
        body=body,
        cookie_header=cookie_header,
        extra_headers=extra_headers,
    )


def needs_browser_setup(payload: StealthRequestPayload) -> bool:
    """Back-compat wrapper — prefer ``payload.needs_browser_setup``."""
    return payload.needs_browser_setup
