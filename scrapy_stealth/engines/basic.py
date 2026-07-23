from __future__ import annotations

from datetime import timedelta
from typing import Any

from scrapy.http import Request, Response

from ..exceptions import StealthDependencyError

try:
    from wreq.blocking import Client
    from wreq.proxy import Proxy
except ImportError as exc:
    StealthDependencyError.check("wreq", exc)

from ..detectors.antibot import AntiBotDetector
from ..exceptions import StealthConnectionError, StealthTimeoutError, raise_stealth
from ..utils.console import console
from ..utils.dns import (
    build_wreq_dns_options,
    dns_fingerprint,
    resolve_dns_overrides,
)
from ..utils.headers import get_default_headers, merge_headers
from ..utils.logger import get_logger
from ..utils.profiles import resolve_browser
from ..utils.response import StealthResponse
from ..utils.session import SessionCache
from .base import BaseEngine

logger = get_logger()

# Client cache key: (http2, frozen host→IP pairs).
# dns_options= on get()/post() is ignored.
_BasicClientKey = tuple[bool, tuple[tuple[str, str], ...]]


class BasicEngine(BaseEngine):
    """Stealth HTTP engine powered by wreq with browser profile impersonation."""

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        super().__init__(profile, timeout)
        self.default_profile = resolve_browser(self._default_profile)
        self._clients: SessionCache[_BasicClientKey, Client] = SessionCache(
            self._make_client
        )

    @staticmethod
    def _make_client(key: _BasicClientKey) -> Client:
        http2, dns_items = key
        kwargs: dict[str, Any] = {"http2_only": http2}
        if dns_options := build_wreq_dns_options(dict(dns_items)):
            kwargs["dns_options"] = dns_options
        return Client(**kwargs)

    def _execute(self, request: Request) -> Response | None:
        ctx = self._ctx(request)
        try:
            emulation = (
                self.default_profile
                if ctx.profile == self._default_profile
                else resolve_browser(ctx.profile)
            )
            headers = merge_headers(
                get_default_headers(ctx.profile),
                dict(request.headers.to_unicode_dict()),
            )

            kwargs: dict[str, Any] = {
                "emulation": emulation,
                "timeout": timedelta(seconds=ctx.timeout),
                "headers": headers,
            }
            if request.body:
                kwargs["data"] = request.body
            if ctx.proxy:
                kwargs["proxy"] = Proxy.all(ctx.proxy)

            dns_overrides = resolve_dns_overrides(request)
            dns_key = dns_fingerprint(dns_overrides)
            if dns_key:
                logger.debug(
                    "Basic engine DNS override(s): %s",
                    dns_overrides,
                )

            logger.debug(
                "Initializing basic stealth client (profile=%s & protocol=%s)",
                ctx.profile,
                "HTTP/2" if ctx.http2 else "HTTP/1.1",
            )

            method_fn = getattr(
                self._clients.get((ctx.http2, dns_key)), request.method.lower()
            )
            resp = method_fn(request.url, **kwargs)

            body = resp.bytes()
            if AntiBotDetector.is_js_challenge_body(body.decode(errors="replace")):
                console.warning(
                    f"JS challenge detected at {request.url!r} — "
                    "switch to driver='browser' to bypass it."
                )

            return StealthResponse(
                request=request,
                status=resp.status.as_int(),
                headers=resp.headers,
                body=body,
                _flags=["basic"],
            )

        except TimeoutError:
            raise
        except Exception as exc:
            from wreq.exceptions import ConnectionError as WConn
            from wreq.exceptions import ProxyConnectionError as WProxyConn
            from wreq.exceptions import TimeoutError as WTimeout

            if isinstance(exc, WTimeout):
                raise_stealth(
                    StealthTimeoutError,
                    f"Basic engine timed out after {ctx.timeout}s fetching {request.url!r}",
                )
            if isinstance(exc, (WConn, WProxyConn)):
                raise_stealth(
                    StealthConnectionError,
                    f"Basic engine connection failed fetching {request.url!r}",
                )
            logger.error("Basic engine request failed: %s", exc)
            return None
