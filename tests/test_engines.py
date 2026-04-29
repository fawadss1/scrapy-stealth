import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import Request, HtmlResponse

from scrapy_stealth.engines.scrapy import ScrapyEngine
from scrapy_stealth.engines.browser import BrowserEngine
from scrapy_stealth.utils.browsers import _BROWSER_MAP, resolve_browser
import rnet


# ---------------------------------------------------------------------------
# ScrapyEngine
# ---------------------------------------------------------------------------

class TestScrapyEngine:
    def test_fetch_returns_none(self):
        engine = ScrapyEngine()
        request = Request("https://example.com")
        spider = MagicMock()
        assert engine.fetch(request, spider) is None


# ---------------------------------------------------------------------------
# resolve_browser
# ---------------------------------------------------------------------------

class TestResolveBrowser:
    def test_none_returns_default(self):
        assert resolve_browser(None) == rnet.Impersonate.Chrome137

    def test_enum_passthrough(self):
        assert resolve_browser(rnet.Impersonate.Chrome137) == rnet.Impersonate.Chrome137

    def test_string_chrome_137(self):
        assert resolve_browser("chrome_137") == rnet.Impersonate.Chrome137

    def test_string_firefox_139(self):
        assert resolve_browser("firefox_139") == rnet.Impersonate.Firefox139

    def test_string_safari_18_5(self):
        assert resolve_browser("safari_18_5") == rnet.Impersonate.Safari18_5

    def test_string_edge_134(self):
        assert resolve_browser("edge_134") == rnet.Impersonate.Edge134

    def test_string_opera_119(self):
        assert resolve_browser("opera_119") == rnet.Impersonate.Opera119

    def test_unknown_string_falls_back_to_default(self):
        assert resolve_browser("unknown_browser_99") == rnet.Impersonate.Chrome137

    def test_backward_compat_chrome_120(self):
        assert resolve_browser("chrome_120") == rnet.Impersonate.Chrome120

    def test_backward_compat_safari_17(self):
        assert resolve_browser("safari_17") == rnet.Impersonate.Safari17_5


class TestBrowserMap:
    def test_all_values_are_rnet_impersonate(self):
        for key, value in _BROWSER_MAP.items():
            assert isinstance(value, rnet.Impersonate), f"{key!r} maps to non-Impersonate value"

    def test_map_is_not_empty(self):
        assert len(_BROWSER_MAP) > 0

    def test_latest_browsers_present(self):
        assert "chrome_137" in _BROWSER_MAP
        assert "firefox_139" in _BROWSER_MAP
        assert "safari_18_5" in _BROWSER_MAP
        assert "edge_134" in _BROWSER_MAP
        assert "opera_119" in _BROWSER_MAP


# ---------------------------------------------------------------------------
# BrowserEngine
# ---------------------------------------------------------------------------

def _make_mock_client(status_code=200, content=b"<html><body>ok</body></html>"):
    mock_resp = MagicMock()
    mock_resp.status_code.as_int.return_value = status_code
    mock_resp.bytes.return_value = content
    mock_resp.encoding = "utf-8"

    mock_client = MagicMock()
    mock_client.request.return_value = mock_resp
    return mock_client


class TestBrowserEngine:
    @pytest.fixture
    def engine(self):
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient") as mock_cls:
            mock_cls.return_value = _make_mock_client()
            yield BrowserEngine()

    @pytest.fixture
    def spider(self):
        return MagicMock()

    def test_fetch_returns_deferred(self, engine, spider):
        from twisted.internet.defer import Deferred
        request = Request("https://example.com")
        result = engine.fetch(request, spider)
        assert isinstance(result, Deferred)

    def test_execute_returns_html_response(self):
        mock_client = _make_mock_client(200, b"<html>hello</html>")
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient", return_value=mock_client):
            engine = BrowserEngine()
            request = Request("https://example.com")
            response = engine._execute(request)

        assert isinstance(response, HtmlResponse)
        assert response.status == 200
        assert b"hello" in response.body

    def test_execute_passes_proxy(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient", return_value=mock_client):
            engine = BrowserEngine()
            request = Request("https://example.com", meta={"proxy": "http://proxy:8080"})
            engine._execute(request)

        call_kwargs = mock_client.request.call_args.kwargs
        assert call_kwargs["proxy"] == "http://proxy:8080"

    def test_execute_no_proxy_when_not_set(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient", return_value=mock_client):
            engine = BrowserEngine()
            request = Request("https://example.com")
            engine._execute(request)

        call_kwargs = mock_client.request.call_args.kwargs
        assert "proxy" not in call_kwargs

    def test_execute_updates_impersonate_when_different(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient", return_value=mock_client):
            engine = BrowserEngine(impersonate="chrome_137")
            request = Request("https://example.com", meta={"impersonate": "firefox_139"})
            engine._execute(request)

        mock_client.update.assert_called_once_with(impersonate=rnet.Impersonate.Firefox139)

    def test_execute_skips_update_when_same_impersonate(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient", return_value=mock_client):
            engine = BrowserEngine(impersonate="chrome_137")
            request = Request("https://example.com", meta={"impersonate": "chrome_137"})
            engine._execute(request)

        mock_client.update.assert_not_called()

    def test_execute_returns_none_on_exception(self):
        mock_client = MagicMock()
        mock_client.request.side_effect = Exception("network error")
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient", return_value=mock_client):
            engine = BrowserEngine()
            request = Request("https://example.com")
            result = engine._execute(request)

        assert result is None

    def test_default_impersonate_is_chrome_137(self):
        with patch("scrapy_stealth.engines.browser.rnet.BlockingClient"):
            engine = BrowserEngine()
        assert engine.default_impersonate == rnet.Impersonate.Chrome137
