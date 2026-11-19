from __future__ import annotations

from urllib.parse import urlparse

from scrapy.http import HtmlResponse, Request

from ...config import config


def effective_response_url(request: Request, url: str | None) -> str:
    """Return *url* when it is a valid http(s) URL; otherwise keep ``request.url``."""
    requested = request.url
    if not url:
        return requested
    candidate = url.strip()
    if not candidate or candidate == requested:
        return requested
    parsed = urlparse(candidate)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return candidate
    return requested


class StealthResponse(HtmlResponse):
    """
    Class for handling HTTP responses with extended functionality and customization.

    The StealthResponse class provides a way to handle HTTP responses while enabling
    modifications to request metadata and handling headers in a dictionary format. It
    inherits from the HtmlResponse class and is designed for specific use cases where
    custom response processing is required.
    """

    def __init__(
        self,
        request: Request,
        status: int,
        headers,
        body: bytes,
        encoding: str | None = None,
        _meta: dict | None = None,
        _flags: list[str] | None = None,
        url: str | None = None,
    ) -> None:

        if _meta:
            updated_meta = request.meta.copy()
            updated_meta.update(_meta)
            request = request.replace(meta=updated_meta)

        effective_url = effective_response_url(request, url)
        if effective_url != request.url:
            request = request.replace(url=effective_url)

        headers_dict = self._to_dict(headers)
        super().__init__(
            url=effective_url,
            status=status,
            headers=headers_dict,
            body=body,
            encoding=encoding,
            request=request,
            flags=[config.get("LOGGER_NAME"), *(_flags or [])],
        )

    @staticmethod
    def _to_dict(headers) -> dict:
        pairs = headers.items() if hasattr(headers, "items") else headers
        return {k.decode() if isinstance(k, bytes) else k: v for k, v in pairs}
