import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import Request, HtmlResponse
from twisted.internet.defer import Deferred

from scrapy_stealth.middlewares.stealth import StealthDownloaderMiddleware


def _make_html_response(url="https://example.com", status=200, body=b"<html>ok</html>"):
    request = Request(url)
    return HtmlResponse(url=url, status=status, body=body, encoding="utf-8", request=request)


class TestStealthDownloaderMiddleware:
    @pytest.fixture
    def spider(self):
        return MagicMock()

    @pytest.fixture
    def middleware(self):
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient"):
            yield StealthDownloaderMiddleware()

    def test_from_crawler_returns_instance(self):
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient"):
            crawler = MagicMock()
            mw = StealthDownloaderMiddleware.from_crawler(crawler)
        assert isinstance(mw, StealthDownloaderMiddleware)

    def test_default_engine_is_scrapy(self, middleware, spider):
        request = Request("https://example.com")
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch.return_value = None
            mock_get.return_value = mock_engine
            middleware.process_request(request, spider)
            mock_get.assert_called_once_with("scrapy")

    def test_stealth_engine_selected_via_meta(self, middleware, spider):
        request = Request("https://example.com", meta={"engine": "stealth"})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch.return_value = None
            mock_get.return_value = mock_engine
            middleware.process_request(request, spider)
            mock_get.assert_called_once_with("stealth")

    def test_returns_none_when_engine_returns_none(self, middleware, spider):
        request = Request("https://example.com")
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch.return_value = None
            mock_get.return_value = mock_engine
            result = middleware.process_request(request, spider)
        assert result is None

    def test_returns_response_when_engine_returns_response(self, middleware, spider):
        response = _make_html_response()
        request = Request("https://example.com", meta={"engine": "stealth"})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch.return_value = response
            mock_get.return_value = mock_engine
            result = middleware.process_request(request, spider)
        assert result is response

    def test_returns_deferred_when_engine_returns_deferred(self, middleware, spider):
        deferred = Deferred()
        request = Request("https://example.com", meta={"engine": "stealth"})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch.return_value = deferred
            mock_get.return_value = mock_engine
            result = middleware.process_request(request, spider)
        assert isinstance(result, Deferred)

    def test_middleware_has_manager(self, middleware):
        from scrapy_stealth.manager import EngineManager
        assert isinstance(middleware.manager, EngineManager)
