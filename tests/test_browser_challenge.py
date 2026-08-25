from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scrapy_stealth.utils.browser._core import (
    _is_binary_body,
    _MainDocumentCapture,
    _should_replace_capture_status,
    _url_looks_binary,
    resolve_browser_get_body,
)


class TestUrlHelpers:
    def test_url_looks_binary_for_jpg(self):
        assert _url_looks_binary("https://scdn.autodoc.de/vehicles/800x287/8145.jpg")

    def test_url_looks_binary_for_png(self):
        assert _url_looks_binary(
            "https://scdn.autodoc.de/catalog/categories/100x100/10564.png"
        )


class TestBinaryBodyHelpers:
    def test_is_binary_body_detects_jpeg(self):
        assert _is_binary_body(b"\xff\xd8\xff\xe0") is True
        assert _is_binary_body(b"<html>") is False

    def test_should_replace_capture_status_prefers_200_over_403(self):
        assert _should_replace_capture_status(403, 200) is True
        assert _should_replace_capture_status(200, 403) is False


class TestResolveBrowserGetBody:
    @pytest.mark.asyncio
    async def test_binary_url_uses_fetch_when_network_body_is_html(self):
        page = AsyncMock()
        capture = _MainDocumentCapture(
            "https://scdn.autodoc.de/vehicles/800x287/8145.jpg"
        )
        capture.get_body = AsyncMock(
            return_value=(
                b"<html><body><img src='8145.jpg'></body></html>",
                {"content-type": "text/html"},
                200,
            )
        )

        with patch(
            "scrapy_stealth.utils.browser.request.browser_binary_fetch",
            new=AsyncMock(
                return_value=(
                    b"\xff\xd8\xff\xe0fakejpeg",
                    200,
                    {"content-type": "image/jpeg"},
                )
            ),
        ) as mock_fetch:
            body, headers, status = await resolve_browser_get_body(
                page,
                "https://scdn.autodoc.de/vehicles/800x287/8145.jpg",
                capture,
            )

        assert body.startswith(b"\xff\xd8\xff")
        assert headers["content-type"] == "image/jpeg"
        assert status == 200
        mock_fetch.assert_awaited_once()


class TestMainDocumentCapture:
    @pytest.mark.asyncio
    async def test_get_body_decodes_base64(self):
        capture = _MainDocumentCapture(
            "https://scdn.autodoc.de/catalog/categories/100x100/10564.png"
        )
        page = AsyncMock()
        capture._page = page
        capture._request_id = "req-1"
        capture._mime_type = "image/png"
        capture._status = 200

        result = MagicMock()
        result.body = "aGVsbG8="
        result.base64_encoded = True

        with patch("nodriver.cdp.network.get_response_body", return_value=MagicMock()):
            page.send = AsyncMock(return_value=result)
            body, headers, status = await capture.get_body()

        assert body == b"hello"
        assert headers["content-type"] == "image/png"
        assert status == 200
