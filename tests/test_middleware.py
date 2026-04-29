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
        with patch("scrapy_stealth.engines.browser.Client"):
            yield StealthDownloaderMiddleware()

    def test_from_crawler_returns_instance(self):
        with patch("scrapy_stealth.engines.browser.Client"):
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

    # -------------------------------------------------------------------
    # rotate_profile
    # -------------------------------------------------------------------

    def test_rotate_profile_sets_impersonate(self, middleware, spider):
        request = Request("https://example.com", meta={"engine": "stealth", "rotate_profile": True})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=MagicMock(return_value=None))
            middleware.process_request(request, spider)
        assert "impersonate" in request.meta

    def test_rotate_profile_does_not_override_explicit_impersonate(self, middleware, spider):
        request = Request(
            "https://example.com",
            meta={"engine": "stealth", "rotate_profile": True, "impersonate": "chrome_137"},
        )
        with patch.object(middleware.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=MagicMock(return_value=None))
            middleware.process_request(request, spider)
        assert request.meta["impersonate"] == "chrome_137"

    def test_rotate_profile_sets_valid_fingerprint(self, middleware, spider):
        from scrapy_stealth.strategies.fingerprint import FINGERPRINTS
        request = Request("https://example.com", meta={"engine": "stealth", "rotate_profile": True})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=MagicMock(return_value=None))
            middleware.process_request(request, spider)
        assert request.meta["impersonate"] in FINGERPRINTS

    # -------------------------------------------------------------------
    # rotate_proxy
    # -------------------------------------------------------------------

    def test_rotate_proxy_sets_proxy_from_list(self, spider):
        proxies = ["http://proxy1:8080", "http://proxy2:8080"]
        with patch("scrapy_stealth.engines.browser.Client"):
            mw = StealthDownloaderMiddleware(proxies=proxies)
        request = Request("https://example.com", meta={"engine": "stealth", "rotate_proxy": True})
        with patch.object(mw.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=MagicMock(return_value=None))
            mw.process_request(request, spider)
        assert request.meta.get("proxy") in proxies

    def test_rotate_proxy_no_op_when_no_proxies(self, middleware, spider):
        request = Request("https://example.com", meta={"engine": "stealth", "rotate_proxy": True})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=MagicMock(return_value=None))
            middleware.process_request(request, spider)
        assert "proxy" not in request.meta

    def test_rotate_proxy_does_not_override_explicit_proxy(self, spider):
        proxies = ["http://proxy1:8080", "http://proxy2:8080"]
        with patch("scrapy_stealth.engines.browser.Client"):
            mw = StealthDownloaderMiddleware(proxies=proxies)
        request = Request(
            "https://example.com",
            meta={"engine": "stealth", "rotate_proxy": True, "proxy": "http://explicit:9999"},
        )
        with patch.object(mw.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=MagicMock(return_value=None))
            mw.process_request(request, spider)
        assert request.meta["proxy"] == "http://explicit:9999"

    def test_from_crawler_reads_stealth_proxies_setting(self, spider):
        crawler = MagicMock()
        crawler.settings.getlist.return_value = ["http://proxy1:8080"]
        with patch("scrapy_stealth.engines.browser.Client"):
            mw = StealthDownloaderMiddleware.from_crawler(crawler)
        crawler.settings.getlist.assert_called_once_with("STEALTH_PROXIES", [])
        assert mw._proxy_rotator.proxies == ["http://proxy1:8080"]
