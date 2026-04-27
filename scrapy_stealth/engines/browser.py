from __future__ import annotations

import datetime
from typing import Any

from wreq.blocking import Client
from wreq.proxy import Proxy
from scrapy.http import HtmlResponse, Request, Response
from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread

from .base import BaseEngine
from ..config import config
from ..utils.browsers import resolve_browser
from ..utils.headers import get_default_headers, merge_headers
from ..utils.logger import get_logger
from ..utils.meta import _get_meta_data

logger = get_logger()


class BrowserEngine(BaseEngine):
    """Stealth HTTP engine with browser profile impersonation."""

    def __init__(
        self,
        profile: str = config.get("DEFAULT_PROFILE"),
        timeout: int = config.get("DEFAULT_TIMEOUT"),
    ):
        self.default_profile = resolve_browser(profile)
        self.timeout = timeout
        self._client = Client()

    def fetch(self, request: Request, spider: Any) -> Response | Deferred | None:
        return deferToThread(self._execute, request)

    def _execute(self, request: Request) -> Response | None:
        try:
            proxy: str | None = _get_meta_data(request, "proxy")
            profile: str = _get_meta_data(request, "profile", config.get("DEFAULT_PROFILE"))
            emulation = resolve_browser(profile)
            timeout_secs: int = _get_meta_data(request, "stealth_timeout", self.timeout)

            headers = merge_headers(
                get_default_headers(profile),
                dict(request.headers.to_unicode_dict()),
            )

            kwargs: dict[str, Any] = {
                "emulation": emulation,
                "timeout": datetime.timedelta(seconds=timeout_secs),
                "headers": headers,
            }
            if request.body:
                kwargs["data"] = request.body
            if proxy:
                kwargs["proxy"] = Proxy.all(proxy)

            method_fn = getattr(self._client, request.method.lower())
            resp = method_fn(request.url, **kwargs)

            return HtmlResponse(
                url=request.url,
                status=resp.status.as_int(),
                headers=resp.headers,
                body=resp.bytes(),
                encoding="utf-8",
                request=request,
                flags=[config.get("LOGGER_NAME")],
            )

        except TimeoutError:
            raise
        except Exception as exc:
            logger.exception("Stealth engine request failed: %s", exc)
            return None
