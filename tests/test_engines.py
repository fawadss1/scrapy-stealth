import pytest
from unittest.mock import MagicMock, patch
from scrapy.http import Request, HtmlResponse

from scrapy_stealth.engines.scrapy import ScrapyEngine
from scrapy_stealth.engines.browser import BrowserEngine
from scrapy_stealth.utils.browsers import _BROWSER_MAP, resolve_browser
from wreq.emulation import Emulation, Profile


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
        assert resolve_browser(None) == Emulation.Chrome147

    def test_enum_passthrough(self):
        assert resolve_browser(Emulation.Chrome147) == Emulation.Chrome147

    def test_string_chrome_137(self):
        assert resolve_browser("chrome_137") == Emulation.Chrome137

    def test_string_firefox_139(self):
        assert resolve_browser("firefox_139") == Emulation.Firefox139

    def test_string_safari_18_5(self):
        assert resolve_browser("safari_18_5") == Emulation.Safari18_5

    def test_string_edge_134(self):
        assert resolve_browser("edge_134") == Emulation.Edge134

    def test_string_opera_119(self):
        assert resolve_browser("opera_119") == Emulation.Opera119

    def test_unknown_string_falls_back_to_default(self):
        assert resolve_browser("unknown_browser_99") == Emulation.Chrome147

    def test_backward_compat_chrome_120(self):
        assert resolve_browser("chrome_120") == Emulation.Chrome120

    def test_backward_compat_safari_17(self):
        assert resolve_browser("safari_17") == Emulation.Safari17_5


class TestBrowserMap:
    def test_all_values_are_emulation(self):
        for key, value in _BROWSER_MAP.items():
            assert isinstance(value, Profile), f"{key!r} maps to non-Profile value"

    def test_map_is_not_empty(self):
        assert len(_BROWSER_MAP) > 0

    def test_latest_browsers_present(self):
        assert "chrome_147" in _BROWSER_MAP
        assert "firefox_149" in _BROWSER_MAP
        assert "safari_26_2" in _BROWSER_MAP
        assert "edge_147" in _BROWSER_MAP
        assert "opera_130" in _BROWSER_MAP


# ---------------------------------------------------------------------------
# BrowserEngine
# ---------------------------------------------------------------------------

def _make_mock_client(status=200, content=b"<html><body>ok</body></html>"):
    mock_status = MagicMock()
    mock_status.as_int.return_value = status

    mock_resp = MagicMock()
    mock_resp.status = mock_status
    mock_resp.bytes.return_value = content
    mock_resp.headers.__getitem__.return_value = b"text/html; charset=utf-8"

    mock_client = MagicMock()
    mock_client.get.return_value = mock_resp
    mock_client.post.return_value = mock_resp
    return mock_client


class TestBrowserEngine:
    @pytest.fixture
    def engine(self):
        with patch("scrapy_stealth.engines.browser.Client") as mock_cls:
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
        with patch("scrapy_stealth.engines.browser.Client", return_value=mock_client):
            engine = BrowserEngine()
            request = Request("https://example.com")
            response = engine._execute(request)

        assert isinstance(response, HtmlResponse)
        assert response.status == 200
        assert b"hello" in response.body

    def test_execute_passes_proxy(self):
        from wreq.proxy import Proxy
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.browser.Client", return_value=mock_client):
            engine = BrowserEngine()
            request = Request("https://example.com", meta={"proxy": "http://proxy:8080"})
            engine._execute(request)

        call_kwargs = mock_client.get.call_args.kwargs
        assert isinstance(call_kwargs["proxy"], Proxy)

    def test_execute_no_proxy_when_not_set(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.browser.Client", return_value=mock_client):
            engine = BrowserEngine()
            request = Request("https://example.com")
            engine._execute(request)

        call_kwargs = mock_client.get.call_args.kwargs
        assert "proxy" not in call_kwargs

    def test_execute_passes_emulation_per_request(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.browser.Client", return_value=mock_client):
            engine = BrowserEngine(impersonate="chrome_137")
            request = Request("https://example.com", meta={"impersonate": "firefox_139"})
            engine._execute(request)

        call_kwargs = mock_client.get.call_args.kwargs
        assert call_kwargs["emulation"] == Emulation.Firefox139

    def test_execute_returns_none_on_exception(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("network error")
        with patch("scrapy_stealth.engines.browser.Client", return_value=mock_client):
            engine = BrowserEngine()
            request = Request("https://example.com")
            result = engine._execute(request)

        assert result is None

    def test_default_impersonate_is_chrome_147(self):
        with patch("scrapy_stealth.engines.browser.Client"):
            engine = BrowserEngine()
        assert engine.default_impersonate == Emulation.Chrome147
