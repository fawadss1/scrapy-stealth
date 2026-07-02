from __future__ import annotations

from typing import Any

from scrapy.http import Request, Response

from ..exceptions import StealthDependencyError

try:
    from curl_cffi import CurlHttpVersion
    from curl_cffi.requests import Session
except ImportError as exc:
    StealthDependencyError.check("curl_cffi", exc)

from ..detectors.antibot import AntiBotDetector
from ..exceptions import StealthConnectionError, StealthTimeoutError, raise_stealth
from ..utils.console import console
from ..utils.headers import _FINGERPRINT_KEYS
from ..utils.logger import get_logger
from ..utils.profiles import resolve_browser
from ..utils.response import StealthResponse
from ..utils.session import SessionCache
from .base import BaseEngine

logger = get_logger()


class TurboEngine(BaseEngine):
    """Stealth HTTP engine with deep TLS fingerprinting (turbo driver)."""

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        super().__init__(profile, timeout)
        self._sessions: SessionCache[Any, Session] = SessionCache(
            lambda impersonate: Session(impersonate=impersonate)
        )

    def _execute(self, request: Request) -> Response | None:
        ctx = self._ctx(request)
        try:
            browser = resolve_browser(ctx.profile, backend="turbo")

            headers = {
                k: v
                for k, v in request.headers.to_unicode_dict().items()
                if k.lower() not in _FINGERPRINT_KEYS
            }

            kwargs: dict[str, Any] = {
                "headers": headers,
                "timeout": ctx.timeout,
                "http_version": CurlHttpVersion.V2_0
                if ctx.http2
                else CurlHttpVersion.V1_1,
            }
            if request.body:
                kwargs["data"] = request.body
            if ctx.proxy:
                kwargs["proxies"] = {"http": ctx.proxy, "https": ctx.proxy}

            logger.debug(
                "Initializing turbo stealth client (profile=%s & protocol=%s)",
                ctx.profile,
                "HTTP/2" if ctx.http2 else "HTTP/1.1",
            )

            session = self._sessions.get(browser)
            method_fn = getattr(session, request.method.lower())
            resp = method_fn(request.url, **kwargs)

            resp_headers = {
                k: v for k, v in resp.headers.items() if k.lower() != "content-encoding"
            }
            if AntiBotDetector.is_js_challenge_body(
                resp.content.decode(errors="replace")
            ):
                console.warning(
                    f"JS challenge detected at {request.url!r} — "
                    "switch to driver='browser' to bypass it."
                )

            return StealthResponse(
                request=request,
                status=resp.status_code,
                headers=resp_headers,
                body=resp.content,
                encoding=resp.encoding,
                _flags=["turbo"],
            )

        except TimeoutError:
            raise
        except Exception as exc:
            from curl_cffi.requests.exceptions import ConnectionError as CurlConn
            from curl_cffi.requests.exceptions import DNSError as CurlDNS
            from curl_cffi.requests.exceptions import ProxyError as CurlProxy
            from curl_cffi.requests.exceptions import Timeout as CurlTimeout

            if isinstance(exc, CurlTimeout):
                raise_stealth(
                    StealthTimeoutError,
                    f"Turbo engine timed out after {ctx.timeout}s fetching {request.url!r}",
                )
            if isinstance(exc, (CurlConn, CurlDNS, CurlProxy)):
                raise_stealth(
                    StealthConnectionError,
                    f"Turbo engine connection failed fetching {request.url!r}",
                )
            logger.error("Turbo engine request failed: %s", exc)
            return None
