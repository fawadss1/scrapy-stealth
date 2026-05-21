from __future__ import annotations

from scrapy.http import HtmlResponse, Request

from ..config import config


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
    def _to_dict(headers) -> dict:
        pairs = headers.items() if hasattr(headers, "items") else headers
        return {k.decode() if isinstance(k, bytes) else k: v for k, v in pairs}
