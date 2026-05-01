from __future__ import annotations

from typing import Any

from curl_cffi import CurlHttpVersion
from curl_cffi.requests import Session
from scrapy.http import Request, Response

from .base import BaseEngine
from ..utils.headers import _FINGERPRINT_KEYS
from ..utils.logger import get_logger
from ..utils.profiles import resolve_browser
from ..utils.response import StealthResponse

logger = get_logger()


class TurboEngine(BaseEngine):
    """Stealth HTTP engine with deep TLS fingerprinting (turbo driver)."""

    def _execute(self, request: Request) -> Response | None:
        try:
            ctx = self._ctx(request)
            browser = resolve_browser(ctx.profile, backend="turbo")

            headers = {
                k: v for k, v in request.headers.to_unicode_dict().items()
                if k.lower() not in _FINGERPRINT_KEYS
            }

            kwargs: dict[str, Any] = {
                "headers": headers,
                "timeout": ctx.timeout,
                "http_version": CurlHttpVersion.V2_0 if ctx.http2 else CurlHttpVersion.V1_1,
            }
            if request.body:
                kwargs["data"] = request.body
            if ctx.proxy:
                kwargs["proxies"] = {"http": ctx.proxy, "https": ctx.proxy}

            logger.debug(
                "Initializing turbo stealth client (profile=%s & protocol=%s)",
                ctx.profile, "HTTP/2" if ctx.http2 else "HTTP/1.1",
            )

            with Session(impersonate=browser) as session:
                method_fn = getattr(session, request.method.lower())
                resp = method_fn(request.url, **kwargs)

            resp_headers = {
                k: v for k, v in resp.headers.items()
                if k.lower() != "content-encoding"
            }
            return StealthResponse(
                request=request,
                status=resp.status_code,
                headers=resp_headers,
                body=resp.content,
                encoding=resp.encoding,
            )

        except TimeoutError:
            raise
        except Exception as exc:
            logger.exception("Turbo engine request failed: %s", exc)
            return None
