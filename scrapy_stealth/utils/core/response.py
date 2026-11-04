from __future__ import annotations

from scrapy.http import HtmlResponse, Request

from ...config import config


def coerce_response_body(body: bytes | memoryview | bytearray) -> bytes:
    """Normalize HTTP body buffers (basic driver may return read-only ``memoryview``)."""
    if isinstance(body, bytes):
        return body
    return bytes(body)


def coerce_http_header(value: bytes | memoryview | str | None) -> str:
    """Normalize header names/values (may be ``memoryview``)."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, memoryview):
        value = bytes(value)
    if isinstance(value, bytes):
        return value.decode("latin-1", errors="replace")
    return str(value)


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
    ) -> None:

        if _meta:
            updated_meta = request.meta.copy()
            updated_meta.update(_meta)
            request = request.replace(meta=updated_meta)

        headers_dict = self._to_dict(headers)
        super().__init__(
            url=request.url,
            status=status,
            headers=headers_dict,
            body=body,
            encoding=encoding,
            request=request,
            flags=[config.get("LOGGER_NAME"), *(_flags or [])],
        )

    @staticmethod
    def _to_dict(headers) -> dict[str, str]:
        pairs = headers.items() if hasattr(headers, "items") else headers
        return {
            coerce_http_header(k): coerce_http_header(v) for k, v in pairs
        }
