import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from scrapy.http import HtmlResponse, Request

from scrapy_stealth.config import config
from scrapy_stealth.middlewares.stealth import StealthDownloaderMiddleware


def _make_html_response(url="https://example.com", status=200, body=b"<html>ok</html>"):
    request = Request(url)
    return HtmlResponse(
        url=url, status=status, body=body, encoding="utf-8", request=request
    )


class TestStealthDownloaderMiddleware:
    @pytest.fixture
    def spider(self):
        return MagicMock()

    @pytest.fixture
    def middleware(self):
        with patch("scrapy_stealth.engines.basic.Client"):
            yield StealthDownloaderMiddleware()

    def test_from_crawler_returns_instance(self):
        with patch("scrapy_stealth.engines.basic.Client"):
            crawler = MagicMock()
            mw = StealthDownloaderMiddleware.from_crawler(crawler)
        assert isinstance(mw, StealthDownloaderMiddleware)

    def test_from_crawler_connects_spider_closed(self):
        with patch("scrapy_stealth.engines.basic.Client"):
            crawler = MagicMock()
            mw = StealthDownloaderMiddleware.from_crawler(crawler)
        connected = [c.args[0] for c in crawler.signals.connect.call_args_list]
        assert mw.spider_opened in connected
        assert mw.spider_closed in connected

    def test_spider_closed_closes_engines(self, middleware, spider):
        with patch.object(middleware.manager, "close") as mock_close:
            middleware.spider_closed(spider)
        mock_close.assert_called_once_with()

    def test_default_engine_is_scrapy(self, middleware, spider):
        request = Request("https://example.com")
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch = AsyncMock(return_value=None)
            mock_get.return_value = mock_engine
            asyncio.run(middleware.process_request(request))
            mock_get.assert_called_once_with(config.get("DEFAULT_ENGINE"), None)

    def test_stealth_engine_selected_via_meta(self, middleware, spider):
        request = Request("https://example.com", meta={"stealth": {}})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.driver_name = "basic"
            mock_engine.fetch = AsyncMock(return_value=None)
            mock_get.return_value = mock_engine
            asyncio.run(middleware.process_request(request))
            mock_get.assert_called_once_with("stealth", None)

    def test_stealth_request_stats_use_resolved_driver(self, spider):
        crawler = MagicMock()
        with patch("scrapy_stealth.engines.basic.Client"):
            middleware = StealthDownloaderMiddleware(crawler=crawler)
        request = Request(
            "https://example.com",
            meta={"stealth": {"driver": "turbo"}},
        )
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.driver_name = "turbo"
            mock_engine.fetch = AsyncMock(return_value=None)
            mock_get.return_value = mock_engine
            asyncio.run(middleware.process_request(request))

        crawler.stats.inc_value.assert_any_call("stealth/requests", 1)
        crawler.stats.inc_value.assert_any_call("stealth/requests/turbo", 1)
        crawler.stats.set_value.assert_called_with("stealth/driver", "turbo")

    def test_process_request_passes_crawler_spider_to_engine(self, spider):
        crawler = MagicMock()
        crawler.spider = spider
        with patch("scrapy_stealth.engines.basic.Client"):
            middleware = StealthDownloaderMiddleware(crawler=crawler)
        request = Request("https://example.com", meta={"stealth": {}})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.driver_name = "basic"
            mock_engine.fetch = AsyncMock(return_value=None)
            mock_get.return_value = mock_engine
            asyncio.run(middleware.process_request(request))
        mock_engine.fetch.assert_awaited_once_with(request, spider)

    def test_process_request_signature_has_no_spider_arg(self):
        import inspect

        params = inspect.signature(
            StealthDownloaderMiddleware.process_request
        ).parameters
        assert "spider" not in params
        assert "request" in params

    def test_returns_none_when_engine_returns_none(self, middleware, spider):
        request = Request("https://example.com")
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch = AsyncMock(return_value=None)
            mock_get.return_value = mock_engine
            result = asyncio.run(middleware.process_request(request))
        assert result is None

    def test_returns_response_when_engine_returns_response(self, middleware, spider):
        response = _make_html_response()
        request = Request("https://example.com", meta={"stealth": {}})
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch = AsyncMock(return_value=response)
            mock_get.return_value = mock_engine
            result = asyncio.run(middleware.process_request(request))
        assert result is response

    def test_process_request_is_coroutine(self, middleware, spider):
        import inspect

        request = Request("https://example.com")
        with patch.object(middleware.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch = AsyncMock(return_value=None)
            mock_get.return_value = mock_engine
            result = middleware.process_request(request)
        assert inspect.iscoroutine(result)
        result.close()

    def test_middleware_has_manager(self, middleware):
        from scrapy_stealth.manager import EngineManager

        assert isinstance(middleware.manager, EngineManager)

    def test_spider_opened_seeds_engine_proxies(self, spider):
        proxies = ["http://proxy1:8080", "http://proxy2:8080"]
        with patch("scrapy_stealth.engines.basic.Client"):
            mw = StealthDownloaderMiddleware(proxies=proxies)
        spider.crawler.settings.getlist.side_effect = lambda key, default=None: (
            proxies if key == "STEALTH_PROXIES" else []
        )
        spider.crawler.settings.getbool.return_value = False
        spider.crawler.settings.get.return_value = None
        original = list(config.STEALTH_PROXIES)
        try:
            mw.spider_opened(spider)
            assert config.STEALTH_PROXIES == proxies
            engine = mw.manager.get("stealth", "basic")
            assert engine._default_proxy in proxies
        finally:
            config.STEALTH_PROXIES = original

    def test_explicit_meta_proxy_overrides_default(self, spider):
        proxies = ["http://proxy1:8080"]
        with patch("scrapy_stealth.engines.basic.Client"):
            mw = StealthDownloaderMiddleware(proxies=proxies)
        config.STEALTH_PROXIES = proxies
        mw.manager.seed_proxies()
        request = Request(
            "https://example.com",
            meta={"stealth": {"proxy": "http://explicit:9999"}},
        )
        with patch.object(mw.manager, "get") as mock_get:
            mock_engine = MagicMock()
            mock_engine.fetch = AsyncMock(return_value=None)
            mock_get.return_value = mock_engine
            asyncio.run(mw.process_request(request))
        assert request.meta["stealth"]["proxy"] == "http://explicit:9999"

    def test_from_crawler_reads_stealth_proxies_setting(self, spider):
        crawler = MagicMock()
        crawler.settings.getlist.return_value = ["http://proxy1:8080"]
        crawler.settings.getbool.return_value = False
        with patch("scrapy_stealth.engines.basic.Client"):
            mw = StealthDownloaderMiddleware.from_crawler(crawler)
        crawler.settings.getlist.assert_called_once_with("STEALTH_PROXIES", [])
        assert mw._proxy_rotator.proxies == ["http://proxy1:8080"]

    # -------------------------------------------------------------------
    # STEALTH_ENABLED
    # -------------------------------------------------------------------

    def test_stealth_enabled_injects_meta_on_plain_request(self, spider):
        with patch("scrapy_stealth.engines.basic.Client"):
            mw = StealthDownloaderMiddleware(stealth_enabled=True)
        request = Request("https://example.com")
        with patch.object(mw.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=AsyncMock(return_value=None))
            asyncio.run(mw.process_request(request))
        assert "stealth" in request.meta
        mock_get.assert_called_once_with("stealth", None)

    def test_stealth_enabled_does_not_override_existing_meta(self, spider):
        with patch("scrapy_stealth.engines.basic.Client"):
            mw = StealthDownloaderMiddleware(stealth_enabled=True)
        request = Request("https://example.com", meta={"stealth": {"driver": "turbo"}})
        with patch.object(mw.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=AsyncMock(return_value=None))
            asyncio.run(mw.process_request(request))
        assert request.meta["stealth"]["driver"] == "turbo"

    def test_stealth_enabled_respects_opt_out(self, spider):
        with patch("scrapy_stealth.engines.basic.Client"):
            mw = StealthDownloaderMiddleware(stealth_enabled=True)
        request = Request("https://example.com", meta={"stealth": False})
        with patch.object(mw.manager, "get") as mock_get:
            mock_get.return_value = MagicMock(fetch=AsyncMock(return_value=None))
            asyncio.run(mw.process_request(request))
        mock_get.assert_called_once_with(config.get("DEFAULT_ENGINE"), None)

    def test_from_crawler_reads_stealth_enabled_setting(self):
        crawler = MagicMock()
        crawler.settings.getlist.return_value = []
        crawler.settings.getbool.return_value = True
        with patch("scrapy_stealth.engines.basic.Client"):
            mw = StealthDownloaderMiddleware.from_crawler(crawler)
        crawler.settings.getbool.assert_called_with("STEALTH_ENABLED", False)
        assert mw._stealth_enabled is True

    # -------------------------------------------------------------------
    # STEALTH_DRIVER
    # -------------------------------------------------------------------

    def test_spider_opened_sets_stealth_driver_from_settings(self, middleware):
        spider = MagicMock()
        spider.crawler.settings.getlist.return_value = []
        spider.crawler.settings.getbool.return_value = False
        spider.crawler.settings.get.side_effect = lambda key, default=None: (
            "turbo" if key == "STEALTH_DRIVER" else None
        )
        original = config.get("STEALTH_DRIVER")
        try:
            middleware.spider_opened(spider)
            assert config.get("STEALTH_DRIVER") == "turbo"
        finally:
            config.STEALTH_DRIVER = original

    def test_spider_opened_no_stealth_driver_leaves_config_unchanged(self, middleware):
        spider = MagicMock()
        spider.crawler.settings.getlist.return_value = []
        spider.crawler.settings.getbool.return_value = False
        spider.crawler.settings.get.return_value = None
        original = config.get("STEALTH_DRIVER")
        middleware.spider_opened(spider)
        assert config.get("STEALTH_DRIVER") == original

    def test_from_crawler_triggers_update_check(self):
        crawler = MagicMock()
        crawler.settings.getlist.return_value = []
        crawler.settings.getbool.return_value = False
        with (
            patch("scrapy_stealth.engines.basic.Client"),
            patch("scrapy_stealth.middlewares.stealth.update_available") as mock_check,
        ):
            StealthDownloaderMiddleware.from_crawler(crawler)
        mock_check.assert_called_once()

    def test_invalid_stealth_driver_in_settings_falls_back_in_manager(
        self, middleware, spider
    ):
        spider.crawler.settings.getlist.return_value = []
        spider.crawler.settings.getbool.return_value = False
        spider.crawler.settings.get.side_effect = lambda key, default=None: (
            "browsesr" if key == "STEALTH_DRIVER" else None
        )
        original = config.get("STEALTH_DRIVER")
        try:
            middleware.spider_opened(spider)
            request = Request("https://example.com", meta={"stealth": {}})
            with patch.object(
                middleware.manager, "get", wraps=middleware.manager.get
            ) as mock_get:
                mock_get.return_value = MagicMock(fetch=AsyncMock(return_value=None))
                asyncio.run(middleware.process_request(request))
            mock_get.assert_called_once_with("stealth", None)
        finally:
            config.STEALTH_DRIVER = original

    # -------------------------------------------------------------------
    # STEALTH_DNS_OVERRIDES
    # -------------------------------------------------------------------

    def test_spider_opened_loads_dns_overrides(self, middleware):
        spider = MagicMock()
        spider.crawler.settings.getlist.return_value = []
        spider.crawler.settings.getbool.return_value = False
        spider.crawler.settings.get.side_effect = lambda key, default=None: (
            {"example.com": "203.0.113.10"} if key == "STEALTH_DNS_OVERRIDES" else None
        )
        original = dict(config.STEALTH_DNS_OVERRIDES)
        try:
            middleware.spider_opened(spider)
            assert config.STEALTH_DNS_OVERRIDES == {"example.com": "203.0.113.10"}
        finally:
            config.STEALTH_DNS_OVERRIDES = original

    def test_spider_opened_rejects_invalid_dns_ip(self, middleware):
        spider = MagicMock()
        spider.crawler.settings.getlist.return_value = []
        spider.crawler.settings.getbool.return_value = False
        spider.crawler.settings.get.side_effect = lambda key, default=None: (
            {"example.com": "not-an-ip"} if key == "STEALTH_DNS_OVERRIDES" else None
        )
        with pytest.raises(ValueError, match="not a valid IPv4/IPv6"):
            middleware.spider_opened(spider)
