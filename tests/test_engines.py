import pytest
from unittest.mock import MagicMock, patch, call
from scrapy.http import Request, HtmlResponse

from curl_cffi import CurlHttpVersion

from scrapy_stealth.config import config
from scrapy_stealth.engines.scrapy import ScrapyEngine
from scrapy_stealth.engines.basic import BasicEngine
from scrapy_stealth.engines.turbo import TurboEngine
from scrapy_stealth.utils.headers import _FINGERPRINT_KEYS
from scrapy_stealth.utils.profiles import _BROWSER_MAP, resolve_browser
from scrapy_stealth.utils.response import StealthResponse
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
    def test_default_profile_string_resolves(self):
        assert resolve_browser(config.get("DEFAULT_PROFILE")) == Emulation.Chrome147

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
# BasicEngine
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


class TestBasicEngine:
    @pytest.fixture
    def engine(self):
        with patch("scrapy_stealth.engines.basic.Client") as mock_cls:
            mock_cls.return_value = _make_mock_client()
            yield BasicEngine()

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
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            request = Request("https://example.com")
            response = engine._execute(request)

        assert isinstance(response, HtmlResponse)
        assert response.status == 200
        assert b"hello" in response.body

    def test_execute_passes_proxy(self):
        from wreq.proxy import Proxy
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            request = Request("https://example.com", meta={"stealth": {"proxy": "http://proxy:8080"}})
            engine._execute(request)

        call_kwargs = mock_client.get.call_args.kwargs
        assert isinstance(call_kwargs["proxy"], Proxy)

    def test_execute_no_proxy_when_not_set(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            request = Request("https://example.com")
            engine._execute(request)

        call_kwargs = mock_client.get.call_args.kwargs
        assert "proxy" not in call_kwargs

    def test_execute_passes_emulation_per_request(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine(profile="chrome_137")
            request = Request("https://example.com", meta={"stealth": {"profile": "firefox_139"}})
            engine._execute(request)

        call_kwargs = mock_client.get.call_args.kwargs
        assert call_kwargs["emulation"] == Emulation.Firefox139

    def test_execute_returns_none_on_exception(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("network error")
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            request = Request("https://example.com")
            result = engine._execute(request)

        assert result is None

    def test_default_profile_matches_config(self):
        with patch("scrapy_stealth.engines.basic.Client"):
            engine = BasicEngine()
        assert engine.default_profile == resolve_browser(config.get("DEFAULT_PROFILE"))


# ---------------------------------------------------------------------------
# TurboEngine
# ---------------------------------------------------------------------------

def _make_turbo_response(status=200, content=b"<html><body>turbo</body></html>", headers=None):
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.content = content
    mock_resp.headers.items.return_value = list((headers or {}).items())
    return mock_resp


def _turbo_session_ctx(mock_resp):
    """Return a Session class mock whose context manager yields a session that returns mock_resp."""
    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    mock_session.post.return_value = mock_resp

    mock_cls = MagicMock()
    mock_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_cls.return_value.__exit__ = MagicMock(return_value=False)
    return mock_cls, mock_session


class TestTurboEngine:
    @pytest.fixture
    def mock_resp(self):
        return _make_turbo_response()

    @pytest.fixture
    def session_patch(self, mock_resp):
        mock_cls, mock_session = _turbo_session_ctx(mock_resp)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            yield mock_cls, mock_session

    def test_fetch_returns_deferred(self, session_patch):
        from twisted.internet.defer import Deferred
        engine = TurboEngine()
        spider = MagicMock()
        result = engine.fetch(Request("https://example.com"), spider)
        assert isinstance(result, Deferred)

    def test_execute_returns_stealth_response(self, session_patch):
        engine = TurboEngine()
        response = engine._execute(Request("https://example.com"))
        assert isinstance(response, StealthResponse)
        assert response.status == 200
        assert b"turbo" in response.body

    def test_execute_uses_http2_version(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com", meta={"stealth": {"http2": True}}))
        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["http_version"] == CurlHttpVersion.V2_0

    def test_execute_uses_http1_version_by_default(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com", meta={"stealth": {"http2": False}}))
        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["http_version"] == CurlHttpVersion.V1_1

    def test_execute_strips_fingerprint_headers(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        fingerprint_header = next(iter(_FINGERPRINT_KEYS)).title()
        request = Request(
            "https://example.com",
            headers={fingerprint_header: "should-be-stripped", "X-Custom": "keep-me"},
        )
        engine._execute(request)
        call_kwargs = mock_session.get.call_args.kwargs
        passed_headers = {k.lower(): v for k, v in call_kwargs["headers"].items()}
        for key in _FINGERPRINT_KEYS:
            assert key not in passed_headers
        assert "x-custom" in passed_headers

    def test_execute_passes_proxy(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com", meta={"stealth": {"proxy": "http://proxy:8080"}}))
        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["proxies"] == {"http": "http://proxy:8080", "https": "http://proxy:8080"}

    def test_execute_no_proxy_when_not_set(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com"))
        call_kwargs = mock_session.get.call_args.kwargs
        assert "proxies" not in call_kwargs

    def test_execute_passes_body_on_post(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com", method="POST", body=b"payload"))
        call_kwargs = mock_session.post.call_args.kwargs
        assert call_kwargs["data"] == b"payload"

    def test_execute_no_data_on_get_without_body(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com"))
        call_kwargs = mock_session.get.call_args.kwargs
        assert "data" not in call_kwargs

    def test_execute_resolves_turbo_profile(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com", meta={"stealth": {"profile": "firefox_139"}}))
        impersonate_arg = mock_cls.call_args.kwargs.get("impersonate") or mock_cls.call_args.args[0]
        assert impersonate_arg == "firefox135"

    def test_execute_returns_none_on_exception(self):
        mock_cls = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(side_effect=Exception("connection error"))
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            result = engine._execute(Request("https://example.com"))
        assert result is None

    def test_execute_reraises_timeout(self):
        mock_cls = MagicMock()
        mock_cls.return_value.__enter__ = MagicMock(side_effect=TimeoutError("timed out"))
        mock_cls.return_value.__exit__ = MagicMock(return_value=False)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            with pytest.raises(TimeoutError):
                engine._execute(Request("https://example.com"))

    def test_execute_drops_content_encoding_header(self, session_patch):
        mock_resp = _make_turbo_response(
            headers={"content-encoding": "gzip", "content-type": "text/html"}
        )
        mock_cls, _ = _turbo_session_ctx(mock_resp)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            response = engine._execute(Request("https://example.com"))
        resp_headers = {
            (k.decode() if isinstance(k, bytes) else k).lower(): v
            for k, v in response.headers.items()
        }
        assert "content-encoding" not in resp_headers
        assert "content-type" in resp_headers
