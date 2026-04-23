from __future__ import annotations

import logging
from typing import Any

import rnet
from scrapy.http import HtmlResponse, Request, Response
from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread

from .base import BaseEngine
from ..constants import DEFAULT_IMPERSONATE, DEFAULT_TIMEOUT
from ..utils.browsers import resolve_browser
from ..utils.headers import get_default_headers, merge_headers
from ..utils.logger import get_logger
from ..utils.meta import _get_meta_data

logger = get_logger()


class BrowserEngine(BaseEngine):
    """Stealth HTTP engine with browser impersonation."""

    def __init__(self, impersonate: str = DEFAULT_IMPERSONATE, timeout: int = DEFAULT_TIMEOUT):
        self.default_impersonate = resolve_browser(impersonate)
        self.timeout = timeout
        self._client = rnet.BlockingClient(
            impersonate=self.default_impersonate,
            timeout=timeout,
        )

    def fetch(self, request: Request, spider: Any) -> Response | Deferred | None:
        return deferToThread(self._execute, request)

    def _execute(self, request: Request) -> Response | None:
        try:
            proxy: str | None = _get_meta_data(request, "proxy")
            profile: str = _get_meta_data(request, "impersonate", DEFAULT_IMPERSONATE)
            impersonate = resolve_browser(profile)

            if impersonate != self.default_impersonate:
                self._client.update(impersonate=impersonate)

            headers = merge_headers(
                get_default_headers(profile),
                dict(request.headers.to_unicode_dict()),
            )

            kwargs: dict[str, Any] = {
                "method": getattr(rnet.Method, request.method.upper()),
                "url": request.url,
                "headers": headers,
            }
            if request.body:
                kwargs["data"] = request.body
            if proxy:
                kwargs["proxy"] = proxy

            resp = self._client.request(**kwargs)

            return HtmlResponse(
                url=request.url,
                status=resp.status_code.as_int(),
                body=resp.bytes(),
                encoding=resp.encoding,
                request=request,
            )

        except TimeoutError:
            raise
        except Exception as exc:
            logger.exception("Stealth engine request failed: %s", exc)
            return None
