from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from scrapy.http import HtmlResponse, Request

from scrapy_stealth.config import config
from scrapy_stealth.middlewares.stealth import StealthDownloaderMiddleware
from scrapy_stealth.utils.browser.cookies import (
    cdp_cookie_to_dict,
    collect_browser_cookies,
    format_cookie_header,
    merge_browser_cookies_to_jar,
    merge_cookie_header,
)


class _FakeCookie:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestBrowserCookieHelpers:
    def test_cdp_cookie_to_dict(self):
        raw = _FakeCookie(
            name="sid",
            value="1",
            domain=".example.com",
            path="/",
            secure=True,
            http_only=True,
            session=False,
            expires=123.0,
        )
        assert cdp_cookie_to_dict(raw) == {
            "name": "sid",
            "value": "1",
            "domain": ".example.com",
            "path": "/",
            "secure": True,
            "httpOnly": True,
            "session": False,
            "expires": 123.0,
        }

    def test_format_cookie_header_deduplicates_names(self):
        cookies = [
            {"name": "a", "value": "1"},
            {"name": "b", "value": "2"},
            {"name": "a", "value": "9"},
        ]
        assert format_cookie_header(cookies) == "a=1; b=2"

    def test_merge_cookie_header(self):
        merged = merge_cookie_header("a=1; old=9", "b=2; a=new")
        assert merged == "a=new; old=9; b=2"

    @pytest.mark.asyncio
    async def test_collect_browser_cookies_uses_get_cookies(self):
        page = AsyncMock()
        page.send = AsyncMock(
            return_value=[
                _FakeCookie(
                    name="session",
                    value="xyz",
                    domain="example.com",
                    path="/",
                    secure=False,
                    http_only=False,
                    session=True,
                    expires=None,
                )
            ]
        )
        cookies = await collect_browser_cookies(page, "https://example.com/page")
        assert cookies == [
            {
                "name": "session",
                "value": "xyz",
                "domain": "example.com",
                "path": "/",
                "secure": False,
                "httpOnly": False,
                "session": True,
                "expires": None,
            }
        ]

    def test_cdp_cookie_to_dict_normalizes_session_expires(self):
        raw = _FakeCookie(
            name="session",
            value="1",
            domain="example.com",
            path="/",
            secure=False,
            http_only=True,
            session=True,
            expires=-1,
        )
        assert cdp_cookie_to_dict(raw)["expires"] is None

    def test_merge_browser_cookies_to_jar_sends_session_cookie(self):
        from scrapy.http.cookies import CookieJar

        jar = CookieJar()
        login = Request("https://example.com/login", method="POST")
        cookies = [
            {
                "name": "session",
                "value": "abc",
                "domain": "example.com",
                "path": "/",
                "secure": False,
                "httpOnly": True,
                "session": True,
                "expires": -1,
            }
        ]
        merged = merge_browser_cookies_to_jar(jar, login, cookies)
        assert merged == 1
        follow_up = Request("https://example.com/")
        jar.add_cookie_header(follow_up)
        assert b"session=abc" in follow_up.headers.get("Cookie", b"")


class TestBrowserCookieMiddleware:
    def test_process_response_merges_cookies_into_jar(self):
        crawler = MagicMock()
        crawler.settings.getbool.return_value = True
        middleware = StealthDownloaderMiddleware(crawler=crawler)
        request = Request("https://example.com/login", method="POST")
        response = HtmlResponse(
            url="https://example.com/login",
            body=b"ok",
            request=request.replace(
                meta={
                    "stealth": {
                        "browser_cookies": [{"name": "a", "value": "1"}],
                        "browser_cookie_header": "a=1",
                    }
                }
            ),
        )
        with (
            pytest.MonkeyPatch.context() as mp,
            patch.object(middleware, "_cookie_jar", return_value=MagicMock()),
            patch(
                "scrapy_stealth.middlewares.stealth.merge_browser_cookies_to_jar",
                return_value=2,
            ) as mock_merge,
        ):
            mp.setattr(config, "BROWSER_EXPORT_COOKIES", True)
            import asyncio

            result = asyncio.run(
                middleware.process_response(request, response, MagicMock())
            )

        assert result is response
        mock_merge.assert_called_once()
        crawler.stats.inc_value.assert_any_call("stealth/browser_cookies_exported", 2)

    def test_process_response_skips_when_export_disabled(self):
        crawler = MagicMock()
        crawler.settings.getbool.return_value = True
        middleware = StealthDownloaderMiddleware(crawler=crawler)
        request = Request("https://example.com/login", method="POST")
        response = HtmlResponse(
            url="https://example.com/login",
            body=b"ok",
            request=request.replace(
                meta={
                    "stealth": {
                        "browser_cookies": [{"name": "a", "value": "1"}],
                    }
                }
            ),
        )
        mock_jar = MagicMock()
        with (
            pytest.MonkeyPatch.context() as mp,
            patch.object(middleware, "_cookie_jar", return_value=mock_jar),
        ):
            mp.setattr(config, "BROWSER_EXPORT_COOKIES", False)
            import asyncio

            asyncio.run(middleware.process_response(request, response, MagicMock()))
        mock_jar.set_cookie_if_ok.assert_not_called()
