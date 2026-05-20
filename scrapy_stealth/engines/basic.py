from __future__ import annotations

from datetime import timedelta
from typing import Any

from wreq.blocking import Client
from wreq.proxy import Proxy
from scrapy.http import Request, Response

from .base import BaseEngine
from ..exceptions import StealthTimeoutError
from ..utils.profiles import resolve_browser
from ..utils.headers import get_default_headers, merge_headers
from ..utils.logger import get_logger
from ..utils.response import StealthResponse
from ..utils.session import SessionCache

logger = get_logger()


class BasicEngine(BaseEngine):
    """Stealth HTTP engine powered by wreq with browser profile impersonation."""

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        super().__init__(profile, timeout)
        self.default_profile = resolve_browser(self._default_profile)
        self._clients: SessionCache[bool, Client] = SessionCache(
            lambda http2: Client(http2_only=http2)
        )

    def _execute(self, request: Request) -> Response | None:
        try:
            ctx = self._ctx(request)
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

            logger.debug(
                "Initializing basic stealth client (profile=%s & protocol=%s)",
                ctx.profile, "HTTP/2" if ctx.http2 else "HTTP/1.1",
            )

            method_fn = getattr(self._clients.get(ctx.http2), request.method.lower())
            resp = method_fn(request.url, **kwargs)

            return StealthResponse(
                request=request,
                status=resp.status.as_int(),
                headers=resp.headers,
                body=resp.bytes(),
            )

        except TimeoutError:
            raise
        except Exception as exc:
            from wreq.exceptions import TimeoutError as WTimeout
            if isinstance(exc, WTimeout):
                raise StealthTimeoutError(str(exc)) from exc
            logger.exception("Basic engine request failed: %s", exc)
            return None
