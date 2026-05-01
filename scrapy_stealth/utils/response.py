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
    ) -> None:
        super().__init__(
            url=request.url,
            status=status,
            headers=self._to_dict(headers),
            body=body,
            encoding="utf-8",
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
