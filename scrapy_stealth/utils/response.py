from __future__ import annotations

from scrapy.http import HtmlResponse, Request

from ..config import config


class StealthResponse(HtmlResponse):
    """HtmlResponse produced by stealth engines."""

    def __init__(
            self,
            request: Request,
            status: int,
            headers,
            body: bytes,
            encoding: str | None = None,
    ) -> None:
        headers_dict = self._to_dict(headers)
        super().__init__(
            url=request.url,
            status=status,
            headers=headers_dict,
            body=body,
            encoding=encoding,
            request=request,
            flags=[config.get("LOGGER_NAME")],
        )

    @staticmethod
    def _to_dict(headers) -> dict:
        pairs = headers.items() if hasattr(headers, "items") else headers
        return {
            k.decode() if isinstance(k, bytes) else k: v
            for k, v in pairs
        }
