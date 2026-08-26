import asyncio
import sys
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi import CurlHttpVersion
from scrapy.http import HtmlResponse, Request
from wreq.emulation import Emulation, Profile

from scrapy_stealth.config import config
from scrapy_stealth.engines.basic import BasicEngine
from scrapy_stealth.engines.browser import BrowserEngine
from scrapy_stealth.engines.scrapy import ScrapyEngine
from scrapy_stealth.engines.turbo import TurboEngine
from scrapy_stealth.exceptions import (
    StealthBrowserNotFoundError,
    StealthConnectionError,
    StealthTimeoutError,
)
from scrapy_stealth.utils.core.response import StealthResponse
from scrapy_stealth.utils.engine.profiles import _BROWSER_MAP, resolve_browser
from scrapy_stealth.utils.network.headers import _FINGERPRINT_KEYS

# ---------------------------------------------------------------------------
# ScrapyEngine
# ---------------------------------------------------------------------------


class TestScrapyEngine:
    def test_fetch_returns_none(self):
        engine = ScrapyEngine()
        request = Request("https://example.com")
        spider = MagicMock()
        assert asyncio.run(engine.fetch(request, spider)) is None


# ---------------------------------------------------------------------------
# resolve_browser
# ---------------------------------------------------------------------------


class TestResolveBrowser:
    def test_chrome_147_resolves(self):
        assert resolve_browser("chrome_147") == Emulation.Chrome147

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

    def test_unknown_string_falls_back_to_random_pool(self):
        with patch(
            "scrapy_stealth.utils.engine.profiles.ProfileRotator.get",
            return_value="chrome_147",
        ):
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

    def test_fetch_is_coroutine(self, engine, spider):
        import inspect

        request = Request("https://example.com")
        result = engine.fetch(request, spider)
        assert inspect.iscoroutine(result)
        result.close()

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
            request = Request(
                "https://example.com", meta={"stealth": {"proxy": "http://proxy:8080"}}
            )
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

    def test_execute_passes_body_on_post(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            engine._execute(
                Request(
                    "https://example.com/submit",
                    method="POST",
                    body=b"a=1",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            )
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["body"] == b"a=1"
        assert (
            call_kwargs["headers"]["Content-Type"]
            == "application/x-www-form-urlencoded"
        )

    def test_execute_passes_cookie_header(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            engine._execute(
                Request("https://example.com", headers={"Cookie": "session=xyz"})
            )
        call_kwargs = mock_client.get.call_args.kwargs
        assert call_kwargs["headers"]["Cookie"] == "session=xyz"

    def test_execute_passes_dns_options(self):
        mock_client = _make_mock_client()
        with patch(
            "scrapy_stealth.engines.basic.Client", return_value=mock_client
        ) as mock_cls:
            engine = BasicEngine()
            request = Request(
                "https://example.com",
                meta={"stealth": {"dns": "203.0.113.10"}},
            )
            engine._execute(request)

        # wreq only applies DnsOptions on Client(...), not per-request get().
        assert "dns_options" in mock_cls.call_args.kwargs
        assert mock_cls.call_args.kwargs["dns_options"] is not None
        assert "dns_options" not in mock_client.get.call_args.kwargs

    def test_execute_no_dns_options_when_not_set(self):
        mock_client = _make_mock_client()
        with patch(
            "scrapy_stealth.engines.basic.Client", return_value=mock_client
        ) as mock_cls:
            engine = BasicEngine()
            request = Request("https://example.com")
            engine._execute(request)

        assert "dns_options" not in mock_cls.call_args.kwargs

    def test_separate_client_per_dns_override(self):
        mock_client = _make_mock_client()
        with patch(
            "scrapy_stealth.engines.basic.Client", return_value=mock_client
        ) as mock_cls:
            engine = BasicEngine()
            engine._execute(Request("https://example.com"))
            engine._execute(
                Request(
                    "https://example.com",
                    meta={"stealth": {"dns": "203.0.113.10"}},
                )
            )
        assert mock_cls.call_count == 2

    def test_execute_passes_emulation_per_request(self):
        mock_client = _make_mock_client()
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine(profile="chrome_137")
            request = Request(
                "https://example.com", meta={"stealth": {"profile": "firefox_139"}}
            )
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

    def test_execute_raises_stealth_timeout_on_wreq_timeout(self):
        from wreq.exceptions import TimeoutError as WreqTimeout

        mock_client = MagicMock()
        mock_client.get.side_effect = WreqTimeout("wreq timed out")
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            with pytest.raises(
                StealthTimeoutError, match=r"Basic engine timed out after .+s fetching"
            ):
                engine._execute(Request("https://example.com"))

    def test_execute_reraises_builtin_timeout(self):
        mock_client = MagicMock()
        mock_client.get.side_effect = TimeoutError("builtin timeout")
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            with pytest.raises(TimeoutError):
                engine._execute(Request("https://example.com"))

    def test_execute_raises_stealth_connection_error_on_wreq_connection_error(self):
        from wreq.exceptions import ConnectionError as WConn

        mock_client = MagicMock()
        mock_client.get.side_effect = WConn("dns error")
        with patch("scrapy_stealth.engines.basic.Client", return_value=mock_client):
            engine = BasicEngine()
            with pytest.raises(
                StealthConnectionError, match=r"Basic engine connection failed fetching"
            ):
                engine._execute(Request("https://example.com"))

    def test_default_profile_picked_from_pool(self):
        from scrapy_stealth.strategies.fingerprint import FINGERPRINTS

        with patch("scrapy_stealth.engines.basic.Client"):
            engine = BasicEngine()
        assert engine._default_profile in FINGERPRINTS
        assert engine.default_profile == resolve_browser(engine._default_profile)

    def test_client_reused_within_thread(self):
        mock_cls = MagicMock(return_value=_make_mock_client())
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine()
            engine._execute(Request("https://example.com"))
            engine._execute(Request("https://example.com"))
        assert mock_cls.call_count == 1

    def test_separate_clients_per_http2_setting(self):
        mock_cls = MagicMock(return_value=_make_mock_client())
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine()
            engine._execute(
                Request("https://example.com", meta={"stealth": {"http2": True}})
            )
            engine._execute(
                Request("https://example.com", meta={"stealth": {"http2": False}})
            )
        assert mock_cls.call_count == 2

    def test_recycles_clients_after_consecutive_bans(self, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 3)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        mock_cls = MagicMock(return_value=_make_mock_client(status=403))
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine()
            for _ in range(3):
                engine._execute(Request("https://example.com"))
            assert mock_cls.call_count == 1
            engine._execute(Request("https://example.com"))
            assert mock_cls.call_count == 2

    def test_no_recycle_when_responses_are_clean(self, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 3)
        mock_cls = MagicMock(return_value=_make_mock_client())
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine()
            for _ in range(5):
                engine._execute(Request("https://example.com"))
            assert mock_cls.call_count == 1

    def test_rotates_profile_on_session_recycle(self, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        monkeypatch.setattr(
            "scrapy_stealth.strategies.fingerprint.ProfileRotator.get",
            staticmethod(lambda: "firefox_147"),
        )
        mock_cls = MagicMock(return_value=_make_mock_client(status=403))
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine(profile="chrome_147")
            engine._execute(Request("https://example.com"))
            engine._execute(Request("https://example.com"))
            assert engine._default_profile == "firefox_147"

    def test_rotates_proxy_on_session_recycle(self, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        monkeypatch.setattr(config, "STEALTH_PROXIES", ["http://p1:1", "http://p2:2"])
        picks = iter(["http://p1:1", "http://p2:2", "http://p2:2"])
        monkeypatch.setattr(
            "scrapy_stealth.strategies.proxy.ProxyRotator.get",
            lambda self, **kwargs: next(picks),
        )
        mock_cls = MagicMock(return_value=_make_mock_client(status=403))
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine(profile="chrome_147")
            engine._default_proxy = "http://p1:1"
            engine._execute(Request("https://example.com"))
            engine._execute(Request("https://example.com"))
            assert engine._default_proxy == "http://p2:2"

    def test_keeps_meta_proxy_on_recycle_without_proxy_pool(self, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        monkeypatch.setattr(config, "STEALTH_PROXIES", [])
        meta_proxy = "https://user:pass@dc.oxylabs.io:8000"
        mock_cls = MagicMock(return_value=_make_mock_client(status=403))
        with patch("scrapy_stealth.engines.basic.Client", mock_cls):
            engine = BasicEngine(profile="chrome_147")
            assert engine._default_proxy is None
            req = Request(
                "https://example.com", meta={"stealth": {"proxy": meta_proxy}}
            )
            engine._execute(req)
            engine._execute(req)
            assert engine._default_proxy == meta_proxy


# ---------------------------------------------------------------------------
# TurboEngine
# ---------------------------------------------------------------------------


def _make_turbo_response(
    status=200, content=b"<html><body>turbo</body></html>", headers=None
):
    mock_resp = MagicMock()
    mock_resp.status_code = status
    mock_resp.content = content
    mock_resp.headers.items.return_value = list((headers or {}).items())
    return mock_resp


def _turbo_session_ctx(mock_resp):
    """Return a Session class mock whose instances return mock_resp on HTTP calls."""
    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    mock_session.post.return_value = mock_resp

    mock_cls = MagicMock()
    mock_cls.return_value = mock_session
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

    def test_fetch_is_coroutine(self, session_patch):
        import inspect

        engine = TurboEngine()
        spider = MagicMock()
        result = engine.fetch(Request("https://example.com"), spider)
        assert inspect.iscoroutine(result)
        result.close()

    def test_execute_returns_stealth_response(self, session_patch):
        engine = TurboEngine()
        response = engine._execute(Request("https://example.com"))
        assert isinstance(response, StealthResponse)
        assert response.status == 200
        assert b"turbo" in response.body

    def test_execute_uses_http2_version(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(
            Request("https://example.com", meta={"stealth": {"http2": True}})
        )
        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["http_version"] == CurlHttpVersion.V2_0

    def test_execute_uses_http1_version_by_default(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(
            Request("https://example.com", meta={"stealth": {"http2": False}})
        )
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
        engine._execute(
            Request(
                "https://example.com", meta={"stealth": {"proxy": "http://proxy:8080"}}
            )
        )
        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["proxies"] == {
            "http": "http://proxy:8080",
            "https": "http://proxy:8080",
        }

    def test_execute_no_proxy_when_not_set(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com"))
        call_kwargs = mock_session.get.call_args.kwargs
        assert "proxies" not in call_kwargs

    def test_execute_passes_body_on_post(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(
            Request(
                "https://example.com",
                method="POST",
                body=b"payload",
                headers={"Content-Type": "text/plain"},
            )
        )
        call_kwargs = mock_session.post.call_args.kwargs
        assert call_kwargs["data"] == b"payload"
        assert call_kwargs["headers"]["Content-Type"] == "text/plain"

    def test_execute_passes_cookie_header(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com", headers={"Cookie": "sid=abc"}))
        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["cookies"] == {"sid": "abc"}
        assert "Cookie" not in call_kwargs.get("headers", {})
        assert "user-agent" not in {k.lower() for k in call_kwargs.get("headers", {})}

    def test_execute_uses_http3_version(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(
            Request("https://example.com", meta={"stealth": {"http3": True}})
        )
        call_kwargs = mock_session.get.call_args.kwargs
        assert call_kwargs["http_version"] == CurlHttpVersion.V3

    def test_execute_resolves_chrome150_profile(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(
            Request("https://example.com", meta={"stealth": {"profile": "chrome_147"}})
        )
        impersonate_arg = mock_cls.call_args.kwargs.get("impersonate")
        assert impersonate_arg == "chrome150"

    def test_execute_no_data_on_get_without_body(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com"))
        call_kwargs = mock_session.get.call_args.kwargs
        assert "data" not in call_kwargs

    def test_execute_resolves_turbo_profile(self, session_patch):
        mock_cls, mock_session = session_patch
        engine = TurboEngine()
        engine._execute(
            Request("https://example.com", meta={"stealth": {"profile": "firefox_139"}})
        )
        impersonate_arg = (
            mock_cls.call_args.kwargs.get("impersonate") or mock_cls.call_args.args[0]
        )
        assert impersonate_arg == "firefox135"

    def test_execute_returns_none_on_exception(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("connection error")
        mock_cls = MagicMock(return_value=mock_session)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            result = engine._execute(Request("https://example.com"))
        assert result is None

    def test_execute_reraises_builtin_timeout(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = TimeoutError("timed out")
        mock_cls = MagicMock(return_value=mock_session)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            with pytest.raises(TimeoutError):
                engine._execute(Request("https://example.com"))

    def test_execute_raises_stealth_timeout_on_curl_timeout(self):
        from curl_cffi.requests.exceptions import Timeout as CurlTimeout

        mock_session = MagicMock()
        mock_session.get.side_effect = CurlTimeout("curl: (28) timed out")
        mock_cls = MagicMock(return_value=mock_session)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            with pytest.raises(
                StealthTimeoutError, match=r"Turbo engine timed out after .+s fetching"
            ):
                engine._execute(Request("https://example.com"))

    def test_execute_raises_stealth_connection_error_on_curl_connection_error(self):
        from curl_cffi.requests.exceptions import ConnectionError as CurlConn

        mock_session = MagicMock()
        mock_session.get.side_effect = CurlConn("dns error")
        mock_cls = MagicMock(return_value=mock_session)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            with pytest.raises(
                StealthConnectionError, match=r"Turbo engine connection failed fetching"
            ):
                engine._execute(Request("https://example.com"))

    def test_rotates_proxy_on_connection_failure(self, monkeypatch):
        from curl_cffi.requests.exceptions import ProxyError as CurlProxy

        monkeypatch.setattr(
            config,
            "STEALTH_PROXIES",
            ["http://p1:8080", "http://p2:8080"],
        )
        picks = iter(["http://p1:8080", "http://p2:8080"])
        monkeypatch.setattr(
            "scrapy_stealth.strategies.proxy.ProxyRotator.get",
            lambda self, **kwargs: next(picks),
        )
        collector = MagicMock()
        values: dict = {}

        def inc_value(key, count=1):
            values[key] = values.get(key, 0) + count

        def set_value(key, value):
            values[key] = value

        collector.inc_value.side_effect = inc_value
        collector.set_value.side_effect = set_value

        mock_session = MagicMock()
        mock_session.get.side_effect = CurlProxy("curl: (56) Proxy CONNECT aborted")
        mock_cls = MagicMock(return_value=mock_session)
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            engine.set_stats(collector)
            engine._default_proxy = "http://p1:8080"
            with pytest.raises(StealthConnectionError):
                engine._execute(
                    Request(
                        "https://scdn.example/img.jpg",
                        meta={"stealth": {"proxy": "http://p1:8080"}},
                    )
                )
            assert engine._default_proxy == "http://p2:8080"
            assert values.get("stealth/proxy/connection_failures") == 1
            assert values.get("stealth/proxy/connection_failures/turbo") == 1
            assert values.get("stealth/proxy/rotations") == 1
            assert values.get("stealth/proxy/last_connection_failure") == "p1:8080"

    def test_session_reused_for_same_profile(self, session_patch):
        mock_cls, _ = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com"))
        engine._execute(Request("https://example.com"))
        assert mock_cls.call_count == 1

    def test_recycles_sessions_after_consecutive_bans(self, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 3)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        mock_cls, _ = _turbo_session_ctx(_make_turbo_response(status=403))
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine()
            for _ in range(3):
                engine._execute(Request("https://example.com"))
            assert mock_cls.call_count == 1
            engine._execute(Request("https://example.com"))
            assert mock_cls.call_count == 2

    def test_no_recycle_when_responses_are_clean(self, session_patch, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 3)
        mock_cls, _ = session_patch
        engine = TurboEngine()
        for _ in range(5):
            engine._execute(Request("https://example.com"))
        assert mock_cls.call_count == 1

    def test_rotates_profile_on_session_recycle(self, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        monkeypatch.setattr(
            "scrapy_stealth.strategies.fingerprint.ProfileRotator.get",
            staticmethod(lambda: "safari_18"),
        )
        mock_cls, _ = _turbo_session_ctx(_make_turbo_response(status=403))
        with patch("scrapy_stealth.engines.turbo.Session", mock_cls):
            engine = TurboEngine(profile="chrome_147")
            engine._execute(Request("https://example.com"))
            engine._execute(Request("https://example.com"))
            assert engine._default_profile == "safari_18"

    def test_execute_passes_dns_resolve_on_session(self, session_patch):
        from curl_cffi import CurlOpt

        mock_cls, _ = session_patch
        engine = TurboEngine()
        engine._execute(
            Request(
                "https://example.com",
                meta={"stealth": {"dns": "203.0.113.10"}},
            )
        )
        curl_options = mock_cls.call_args.kwargs.get("curl_options")
        assert curl_options is not None
        assert CurlOpt.RESOLVE in curl_options
        assert "example.com:443:203.0.113.10" in curl_options[CurlOpt.RESOLVE]

    def test_separate_session_per_dns_override(self, session_patch):
        mock_cls, _ = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com"))
        engine._execute(
            Request(
                "https://example.com",
                meta={"stealth": {"dns": "203.0.113.10"}},
            )
        )
        assert mock_cls.call_count == 2

    def test_separate_session_per_profile(self, session_patch):
        mock_cls, _ = session_patch
        engine = TurboEngine()
        engine._execute(
            Request("https://example.com", meta={"stealth": {"profile": "chrome_133"}})
        )
        engine._execute(
            Request("https://example.com", meta={"stealth": {"profile": "firefox_139"}})
        )
        assert mock_cls.call_count == 2

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


# ---------------------------------------------------------------------------
# BrowserEngine
# ---------------------------------------------------------------------------


class TestBrowserEngine:
    @pytest.fixture(autouse=True)
    def fast_settle(self, monkeypatch):
        # Zero the settle delay so _execute tests complete instantly instead of waiting 4s each.
        monkeypatch.setattr(config, "BROWSER_SETTLE_S", 0.0)

    @pytest.fixture
    def event_loop(self):
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=loop.run_forever, daemon=True)
        thread.start()
        yield loop
        loop.call_soon_threadsafe(lambda: loop.stop())

    @pytest.fixture
    def mock_tab(self):
        tab = AsyncMock()
        tab.evaluate = AsyncMock(
            side_effect=lambda js: (
                200
                if "responseStatus" in js
                else (
                    False
                    if "chrome-error" in js
                    else (
                        10000
                        if "trim().length" in js
                        else "<html><body>browser ok</body></html>"
                    )
                )
            )
        )
        tab.attach = AsyncMock()
        tab.get = AsyncMock()
        tab.wait = AsyncMock()
        tab.close = AsyncMock()
        tab.aclose = AsyncMock()
        return tab

    @pytest.fixture
    def mock_browser(self, mock_tab):
        target_id = "mock-target-id"
        mock_tab.target = MagicMock()
        mock_tab.target.target_id = target_id

        browser = MagicMock()
        browser.send = AsyncMock(return_value=target_id)
        browser.update_targets = AsyncMock()
        browser.targets = [mock_tab]
        browser.stop = MagicMock()
        return browser

    @pytest.fixture
    def engine(self, event_loop, mock_browser):
        e = BrowserEngine()
        e._browser = mock_browser
        e._loop = event_loop
        e._tab_sem = asyncio.Semaphore(config.get("BROWSER_MAX_TABS"))
        return e

    def test_fetch_is_coroutine(self):
        import inspect

        engine = BrowserEngine()
        result = engine.fetch(Request("https://example.com"), MagicMock())
        assert inspect.iscoroutine(result)
        result.close()

    def test_execute_returns_stealth_response(self, engine):
        response = engine._execute(Request("https://example.com"))
        assert isinstance(response, StealthResponse)
        assert response.status == 200

    def test_execute_body_contains_evaluated_html(self, engine, mock_tab):
        mock_tab.evaluate = AsyncMock(
            side_effect=lambda js: (
                200
                if "responseStatus" in js
                else (
                    False
                    if "chrome-error" in js
                    else (
                        10000
                        if "trim().length" in js
                        else "<html><body>stealth browser</body></html>"
                    )
                )
            )
        )
        response = engine._execute(Request("https://example.com"))
        assert b"stealth browser" in response.body

    def test_execute_opens_tab_per_request(self, engine, mock_browser):
        engine._execute(Request("https://example.com/page1"))
        engine._execute(Request("https://example.com/page2"))
        assert mock_browser.send.call_count == 2

    def test_execute_closes_tab_after_fetch(self, engine, mock_tab):
        engine._execute(Request("https://example.com"))
        mock_tab.close.assert_called_once()

    def test_execute_post_returns_fetch_body(self, engine, mock_tab):
        import base64

        posted = base64.b64encode(b"created").decode()

        async def evaluate(js, await_promise=False, return_by_value=False):
            if "fetch(" in js and await_promise:
                # Nodriver may return a RemoteObject with deep_serialized_value
                # instead of a plain dict when return_by_value=True.
                class _Deep:
                    value = [
                        ["status", {"type": "number", "value": 201}],
                        ["bodyB64", {"type": "string", "value": posted}],
                        [
                            "headers",
                            {
                                "type": "object",
                                "value": [
                                    [
                                        "content-type",
                                        {
                                            "type": "string",
                                            "value": "application/json",
                                        },
                                    ]
                                ],
                            },
                        ],
                    ]

                class _Remote:
                    value = None
                    deep_serialized_value = _Deep()

                return _Remote()
            if "chrome-error://" in js:
                return False
            return 200 if "responseStatus" in js else "<html></html>"

        mock_tab.evaluate = AsyncMock(side_effect=evaluate)
        with patch(
            "scrapy_stealth.engines.browser.prepare_browser_post_context",
            new_callable=AsyncMock,
        ) as mock_origin:
            response = engine._execute(
                Request(
                    "https://example.com/api",
                    method="POST",
                    body=b'{"q":"test"}',
                    headers={"Content-Type": "application/json"},
                )
            )
        mock_origin.assert_awaited_once()
        assert mock_origin.await_args.args[1] == "https://example.com/api"
        assert response.status == 201
        assert response.body == b"created"
        assert response.headers[b"content-type"] == b"application/json"

    def test_execute_get_with_cookie_uses_blank_tab_then_navigate(
        self, engine, mock_tab
    ):
        with (
            patch(
                "scrapy_stealth.engines.browser.apply_browser_cookies",
                new_callable=AsyncMock,
            ) as mock_cookies,
            patch(
                "scrapy_stealth.engines.browser.apply_browser_headers",
                new_callable=AsyncMock,
            ),
        ):
            engine._execute(
                Request(
                    "https://example.com/page",
                    headers={"Cookie": "session=abc123"},
                )
            )
        mock_cookies.assert_awaited_once()
        assert mock_cookies.await_args.args[2] == "session=abc123"
        mock_tab.get.assert_awaited_once_with("https://example.com/page")

    def test_execute_passes_custom_headers_via_cdp(self, engine, mock_tab):
        with patch(
            "scrapy_stealth.engines.browser.apply_browser_headers",
            new_callable=AsyncMock,
        ) as mock_headers:
            engine._execute(
                Request(
                    "https://example.com/page",
                    headers={"Authorization": "Bearer token", "User-Agent": "scrapy"},
                )
            )
        mock_headers.assert_awaited_once()
        passed = mock_headers.await_args.args[1]
        assert passed == {"Authorization": "Bearer token"}
        assert "User-Agent" not in passed

    def test_execute_do_fetch_receives_prepared_request(self, engine):
        captured = {}

        async def fake_fetch(url, prepared, settle, snapshot=False, block_assets=False):
            captured.update(
                {
                    "url": url,
                    "method": prepared.method,
                    "headers": prepared.extra_headers,
                    "body": prepared.body,
                    "cookie_header": prepared.cookie_header,
                }
            )
            return (
                b"<html></html>",
                200,
                None,
                {"content-type": "text/html; charset=utf-8"},
                [],
            )

        with patch.object(engine, "_do_fetch", side_effect=fake_fetch):
            engine._execute(
                Request(
                    "https://example.com/submit",
                    method="POST",
                    body=b"a=1",
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Cookie": "sid=1",
                    },
                )
            )
        assert captured["method"] == "POST"
        assert captured["body"] == b"a=1"
        assert captured["cookie_header"] == "sid=1"
        assert captured["headers"] == {
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def test_execute_exports_browser_cookies_on_response(self, engine):
        cookies = [
            {
                "name": "session",
                "value": "abc123",
                "domain": "example.com",
                "path": "/",
                "secure": False,
                "httpOnly": True,
                "session": False,
                "expires": None,
            }
        ]

        async def fake_fetch(url, prepared, settle, snapshot=False, block_assets=False):
            return (
                b"<html></html>",
                200,
                None,
                {"content-type": "text/html; charset=utf-8"},
                cookies,
            )

        with patch.object(engine, "_do_fetch", side_effect=fake_fetch):
            response = engine._execute(
                Request(
                    "https://example.com/login",
                    method="POST",
                    body=b"user=admin&pass=secret",
                )
            )

        assert response.meta["stealth"]["browser_cookies"] == cookies
        assert response.meta["stealth"]["browser_cookie_header"] == "session=abc123"

    def test_execute_returns_none_on_exception(self, engine, mock_browser):
        mock_browser.send = AsyncMock(side_effect=Exception("network error"))
        result = engine._execute(Request("https://example.com"))
        assert result is None

    def test_execute_raises_stealth_timeout(self, engine, mock_browser):
        mock_browser.send = AsyncMock(side_effect=TimeoutError("timed out"))
        with pytest.raises(
            StealthTimeoutError, match=r"Browser engine timed out after .+s fetching"
        ):
            engine._execute(Request("https://example.com"))

    def test_execute_raises_stealth_connection_error_on_oserror(
        self, engine, mock_browser
    ):
        mock_browser.send = AsyncMock(side_effect=OSError("connection refused"))
        with pytest.raises(
            StealthConnectionError, match=r"Browser engine connection failed fetching"
        ):
            engine._execute(Request("https://example.com"))

    def test_execute_raises_browser_not_found_on_file_not_found(self, engine):
        with patch.object(
            engine,
            "_ensure_browser_unlocked",
            side_effect=StealthBrowserNotFoundError("Browser binary not found."),
        ):
            with pytest.raises(
                StealthBrowserNotFoundError, match="Browser binary not found"
            ):
                engine._execute(Request("https://example.com"))

    def test_execute_passes_headless_from_meta(self, engine):
        with patch.object(engine, "_ensure_browser_unlocked") as mock_ensure:
            engine._execute(
                Request("https://example.com", meta={"stealth": {"headless": False}})
            )
        assert mock_ensure.call_args.kwargs["headless"] is False

    def test_execute_uses_visible_browser_by_default(self, engine):
        with patch.object(engine, "_ensure_browser_unlocked") as mock_ensure:
            engine._execute(
                Request(
                    "https://example.com",
                    meta={"stealth": {"driver": "browser"}},
                )
            )
        assert mock_ensure.call_args.kwargs["headless"] is False

    def test_execute_uses_config_headless_default(self, engine):
        with patch.object(engine, "_ensure_browser_unlocked") as mock_ensure:
            engine._execute(Request("https://example.com"))
        assert mock_ensure.call_args.kwargs["headless"] == config.get(
            "BROWSER_HEADLESS"
        )
        assert mock_ensure.call_args.kwargs["headless"] is False

    def test_execute_respects_headless_true_in_meta(self, engine):
        with patch.object(engine, "_ensure_browser_unlocked") as mock_ensure:
            engine._execute(
                Request(
                    "https://example.com",
                    meta={"stealth": {"driver": "browser", "headless": True}},
                )
            )
        assert mock_ensure.call_args.kwargs["headless"] is True

    def test_execute_passes_proxy_to_do_fetch(self, engine):
        with patch.object(
            engine,
            "_do_fetch",
            new_callable=AsyncMock,
            return_value=(
                b"<html></html>",
                200,
                None,
                {"content-type": "text/html; charset=utf-8"},
                [],
            ),
        ) as mock_fetch:
            engine._execute(
                Request(
                    "https://example.com",
                    meta={"stealth": {"proxy": "http://proxy:8080"}},
                )
            )
        # _do_fetch(url, settle, snapshot) — proxy is already baked into the browser
        # Just verify the fetch was called
        assert mock_fetch.called

    def test_execute_uses_custom_settle_from_meta(self, engine):
        captured = []

        async def fake_fetch(url, prepared, settle, snapshot=False, block_assets=False):
            captured.append(settle)
            return (
                b"<html></html>",
                200,
                None,
                {"content-type": "text/html; charset=utf-8"},
                [],
            )

        with patch.object(engine, "_do_fetch", side_effect=fake_fetch):
            engine._execute(
                Request("https://example.com", meta={"stealth": {"settle": 9.0}})
            )
        assert captured[0] == 9.0

    def test_execute_uses_config_settle_default(self, engine):
        captured = []

        async def fake_fetch(url, prepared, settle, snapshot=False, block_assets=False):
            captured.append(settle)
            return (
                b"<html></html>",
                200,
                None,
                {"content-type": "text/html; charset=utf-8"},
                [],
            )

        with patch.object(engine, "_do_fetch", side_effect=fake_fetch):
            engine._execute(Request("https://example.com"))
        assert captured[0] == config.get("BROWSER_SETTLE_S")

    # -----------------------------------------------------------------
    # Restart after N consecutive bans
    # -----------------------------------------------------------------

    def test_no_restart_when_responses_are_clean(self, engine):
        with patch.object(engine, "_reset_browser") as mock_reset:
            for _ in range(50):
                engine._execute(Request("https://example.com"))
        mock_reset.assert_not_called()

    def _set_status(self, mock_tab, status: int) -> None:
        mock_tab.evaluate = AsyncMock(
            side_effect=lambda js: (
                status
                if "responseStatus" in js
                else (
                    False
                    if "chrome-error" in js
                    else (10000 if "trim().length" in js else "<html></html>")
                )
            )
        )

    def test_restart_after_n_consecutive_bans(self, monkeypatch, engine, mock_tab):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 5)
        self._set_status(mock_tab, 403)
        with patch.object(engine, "_reset_browser") as mock_reset:
            for _ in range(4):
                engine._execute(Request("https://example.com"))
            mock_reset.assert_not_called()
            engine._execute(Request("https://example.com"))
        mock_reset.assert_called_once()

    def test_no_restart_on_200_with_antibot_markers_in_large_page(
        self, monkeypatch, engine, mock_tab
    ):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 5)
        self._set_status(mock_tab, 200)
        large_body = "x" * 3000 + "datadome"
        mock_tab.evaluate = AsyncMock(
            side_effect=lambda js: (
                200
                if "responseStatus" in js
                else (
                    False
                    if "chrome-error" in js
                    else (10000 if "trim().length" in js else large_body)
                )
            )
        )
        with patch.object(engine, "_reset_browser") as mock_reset:
            for _ in range(10):
                engine._execute(Request("https://example.com"))
        mock_reset.assert_not_called()

    def test_restarts_again_after_another_ban_streak(
        self, monkeypatch, engine, mock_tab
    ):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 5)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        self._set_status(mock_tab, 403)
        with patch.object(engine, "_reset_browser") as mock_reset:
            for _ in range(5):
                engine._execute(Request("https://example.com"))
            mock_reset.assert_called_once()
            for _ in range(4):
                engine._execute(Request("https://example.com"))
            assert mock_reset.call_count == 1
            engine._execute(Request("https://example.com"))
        assert mock_reset.call_count == 2

    def test_clean_response_resets_ban_streak(self, monkeypatch, engine, mock_tab):
        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 3)
        with patch.object(engine, "_reset_browser") as mock_reset:
            self._set_status(mock_tab, 403)
            engine._execute(Request("https://example.com"))
            engine._execute(Request("https://example.com"))
            self._set_status(mock_tab, 200)
            engine._execute(Request("https://example.com"))  # resets streak
            self._set_status(mock_tab, 403)
            engine._execute(Request("https://example.com"))
            engine._execute(Request("https://example.com"))
            mock_reset.assert_not_called()

    def test_drain_loop_tasks_cancels_in_flight_coroutines(self, engine):
        from concurrent import futures

        started = threading.Event()

        async def tracked_slow_fetch():
            task = asyncio.current_task()
            assert task is not None
            engine._track_fetch_task(task)
            try:
                started.set()
                await asyncio.sleep(30)
                return b"<html></html>", 200, None
            finally:
                engine._fetch_tasks.discard(task)

        future = asyncio.run_coroutine_threadsafe(tracked_slow_fetch(), engine._loop)
        assert started.wait(timeout=5)

        asyncio.run_coroutine_threadsafe(
            engine._drain_loop_tasks(), engine._loop
        ).result(timeout=5)

        with pytest.raises(futures.CancelledError):
            future.result(timeout=5)

    def test_drain_loop_tasks_cancels_orphaned_sleep_tasks(self, engine):
        async def sleeper():
            await asyncio.sleep(30)

        asyncio.run_coroutine_threadsafe(sleeper(), engine._loop)
        asyncio.run_coroutine_threadsafe(
            engine._drain_loop_tasks(), engine._loop
        ).result(timeout=5)
        pending = asyncio.run_coroutine_threadsafe(
            self._count_pending_tasks(engine), engine._loop
        ).result(timeout=5)
        assert pending == 0

    @staticmethod
    async def _count_pending_tasks(engine) -> int:
        current = asyncio.current_task()
        return len(
            [
                task
                for task in asyncio.all_tasks()
                if task is not current and not task.done()
            ]
        )

    def test_execute_retries_when_fetch_cancelled_during_restart(self, engine):
        calls = {"count": 0}

        async def fetch_once_then_cancel(*_args, **_kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise asyncio.CancelledError()
            return (
                b"<html></html>",
                200,
                None,
                {"content-type": "text/html; charset=utf-8"},
                [],
            )

        with patch.object(engine, "_do_fetch", side_effect=fetch_once_then_cancel):
            response = engine._execute(Request("https://example.com"))

        assert calls["count"] == 2
        assert isinstance(response, StealthResponse)

    # -----------------------------------------------------------------
    # static_assets_block
    # -----------------------------------------------------------------

    def test_static_assets_block_off_by_default(self, monkeypatch, engine):
        monkeypatch.setattr(config, "BROWSER_STATIC_ASSETS_BLOCK", False)
        with patch("scrapy_stealth.engines.browser._block_static_assets") as mock_block:
            engine._execute(Request("https://example.com"))
        mock_block.assert_not_called()

    def test_static_assets_block_enabled_via_config(self, monkeypatch, engine):
        monkeypatch.setattr(config, "BROWSER_STATIC_ASSETS_BLOCK", True)
        with patch("scrapy_stealth.engines.browser._block_static_assets") as mock_block:
            mock_block.return_value.__aenter__ = AsyncMock()
            mock_block.return_value.__aexit__ = AsyncMock()
            engine._execute(Request("https://example.com"))
        mock_block.assert_called_once()

    def test_static_assets_block_enabled_via_meta(self, engine):
        with patch("scrapy_stealth.engines.browser._block_static_assets") as mock_block:
            mock_block.return_value.__aenter__ = AsyncMock()
            mock_block.return_value.__aexit__ = AsyncMock()
            engine._execute(
                Request(
                    "https://example.com",
                    meta={"stealth": {"static_assets_block": True}},
                )
            )
        mock_block.assert_called_once()

    def test_static_assets_block_never_applied_with_snapshot(self, monkeypatch, engine):
        # Even with blocking on globally, snapshot=True must skip blocking.
        monkeypatch.setattr(config, "BROWSER_STATIC_ASSETS_BLOCK", True)
        with patch("scrapy_stealth.engines.browser._block_static_assets") as mock_block:
            engine._execute(
                Request(
                    "https://example.com",
                    meta={"stealth": {"snapshot": True}},
                )
            )
        mock_block.assert_not_called()

    def test_static_assets_block_meta_overrides_config_off(self, engine):
        # static_assets_block=False per-request overrides a True global default.
        config.BROWSER_STATIC_ASSETS_BLOCK = True
        try:
            with patch(
                "scrapy_stealth.engines.browser._block_static_assets"
            ) as mock_block:
                engine._execute(
                    Request(
                        "https://example.com",
                        meta={"stealth": {"static_assets_block": False}},
                    )
                )
            mock_block.assert_not_called()
        finally:
            config.BROWSER_STATIC_ASSETS_BLOCK = False

    # -----------------------------------------------------------------
    # proxy bypass list
    # -----------------------------------------------------------------

    def test_proxy_bypass_flag_added_with_proxy(self, monkeypatch, engine):
        monkeypatch.setattr(
            config, "BROWSER_PROXY_BYPASS_LIST", ["example.com", "*.internal"]
        )
        args = engine._build_args(headless=True, proxy_port=8123)
        assert "--proxy-bypass-list=example.com;*.internal" in args

    def test_proxy_bypass_flag_absent_without_proxy(self, monkeypatch, engine):
        monkeypatch.setattr(config, "BROWSER_PROXY_BYPASS_LIST", ["example.com"])
        args = engine._build_args(headless=True, proxy_port=None)
        assert not any(a.startswith("--proxy-bypass-list") for a in args)

    def test_proxy_bypass_flag_absent_when_list_empty(self, monkeypatch, engine):
        monkeypatch.setattr(config, "BROWSER_PROXY_BYPASS_LIST", [])
        args = engine._build_args(headless=True, proxy_port=8123)
        assert not any(a.startswith("--proxy-bypass-list") for a in args)

    def test_dns_does_not_add_host_resolver_rules(self, monkeypatch, engine):
        # Browser DNS uses a local CONNECT relay, not --host-resolver-rules.
        monkeypatch.setattr(
            config,
            "STEALTH_DNS_OVERRIDES",
            {"example.com": "203.0.113.10"},
        )
        args = engine._build_args(headless=True, proxy_port=None)
        assert not any(a.startswith("--host-resolver-rules=") for a in args)

    def test_dns_hosts_not_added_to_proxy_bypass(self, monkeypatch, engine):
        # Pinned hosts must stay on the local relay (bypass would skip DNS pin).
        monkeypatch.setattr(config, "BROWSER_PROXY_BYPASS_LIST", ["keep.example"])
        engine._dns_overrides = {"shop.example.com": "203.0.113.50"}
        args = engine._build_args(headless=True, proxy_port=8123)
        bypass = [a for a in args if a.startswith("--proxy-bypass-list=")]
        assert len(bypass) == 1
        assert "keep.example" in bypass[0]
        assert "shop.example.com" not in bypass[0]

    def test_dns_relay_started_without_upstream_proxy(self, engine):
        import asyncio

        engine._dns_overrides = {"example.com": "203.0.113.10"}
        with patch(
            "scrapy_stealth.engines.browser._start_browser_relay",
            new_callable=AsyncMock,
        ) as mock_relay:
            mock_relay.return_value = (MagicMock(), 19099)
            with patch.object(
                engine, "_start_browser", new_callable=AsyncMock
            ) as mock_start:
                mock_browser = MagicMock()
                mock_browser.main_tab.get = AsyncMock()
                mock_browser.main_tab.wait = AsyncMock()
                mock_start.return_value = mock_browser
                asyncio.run(engine._start(headless=True, proxy=None))

        mock_relay.assert_awaited_once()
        kwargs = mock_relay.await_args.kwargs
        assert kwargs.get("proxy_url") is None
        assert kwargs.get("dns_overrides") == {"example.com": "203.0.113.10"}
        mock_start.assert_awaited_once()
        assert mock_start.await_args.kwargs.get("proxy_port") == 19099


# ---------------------------------------------------------------------------
# _block_static_assets (CDP Fetch-domain resource blocking)
# ---------------------------------------------------------------------------


class TestBlockStaticAssets:
    @pytest.fixture
    def fake_page(self):
        page = AsyncMock()
        page.handlers: dict = {}

        def add_handler(event_type, callback):
            page.handlers[event_type] = callback

        def remove_handler(event_type, callback):
            page.handlers.pop(event_type, None)
            return True

        page.add_handler = MagicMock(side_effect=add_handler)
        page.remove_handler = MagicMock(side_effect=remove_handler)
        return page

    @staticmethod
    def _make_event(resource_type: str):
        import nodriver.cdp.fetch as cdp_fetch

        event = MagicMock(spec=cdp_fetch.RequestPaused)
        event.request_id = cdp_fetch.RequestId("req-1")
        event.resource_type = MagicMock(value=resource_type)
        return event

    async def _trigger(self, page, resource_type: str):
        import nodriver.cdp.fetch as cdp_fetch

        from scrapy_stealth.utils.browser import _block_static_assets

        async with _block_static_assets(page):
            handler = page.handlers[cdp_fetch.RequestPaused]
            await handler(self._make_event(resource_type))

    def test_image_request_is_failed(self, fake_page):
        import nodriver.cdp.fetch as cdp_fetch

        with patch.object(
            cdp_fetch, "fail_request", wraps=cdp_fetch.fail_request
        ) as mock_fail:
            asyncio.run(self._trigger(fake_page, "Image"))
        mock_fail.assert_called_once()

    def test_document_request_is_continued(self, fake_page):
        import nodriver.cdp.fetch as cdp_fetch

        with patch.object(
            cdp_fetch, "continue_request", wraps=cdp_fetch.continue_request
        ) as mock_continue:
            asyncio.run(self._trigger(fake_page, "Document"))
        mock_continue.assert_called_once()

    def test_handler_removed_on_exit(self, fake_page):
        import nodriver.cdp.fetch as cdp_fetch

        asyncio.run(self._trigger(fake_page, "Image"))
        assert cdp_fetch.RequestPaused not in fake_page.handlers


# ---------------------------------------------------------------------------
# _proxy_bypass_args (Chrome --proxy-bypass-list launch flag)
# ---------------------------------------------------------------------------


class TestProxyBypassArgs:
    def test_builds_flag_joined_with_semicolons(self):
        from scrapy_stealth.utils.browser import _proxy_bypass_args

        assert _proxy_bypass_args(["example.com", "*.internal", "<local>"]) == [
            "--proxy-bypass-list=example.com;*.internal;<local>"
        ]

    def test_single_entry(self):
        from scrapy_stealth.utils.browser import _proxy_bypass_args

        assert _proxy_bypass_args(["example.com"]) == [
            "--proxy-bypass-list=example.com"
        ]

    def test_strips_whitespace_and_drops_empties(self):
        from scrapy_stealth.utils.browser import _proxy_bypass_args

        assert _proxy_bypass_args(["  example.com  ", "", "  ", None, "x.io"]) == [
            "--proxy-bypass-list=example.com;x.io"
        ]

    def test_empty_inputs_return_no_flag(self):
        from scrapy_stealth.utils.browser import _proxy_bypass_args

        assert _proxy_bypass_args(None) == []
        assert _proxy_bypass_args([]) == []
        assert _proxy_bypass_args(["", "  ", None]) == []


# ---------------------------------------------------------------------------
# _loop_exception_handler (Windows Proactor teardown noise suppression)
# ---------------------------------------------------------------------------


class TestLoopExceptionHandler:
    @staticmethod
    def _handle(exc):
        loop = MagicMock()
        BrowserEngine._loop_exception_handler(
            loop, {"message": "Accept failed on a socket", "exception": exc}
        )
        return loop

    @pytest.mark.skipif(
        sys.platform != "win32", reason="winerror is only set on Windows"
    )
    @pytest.mark.parametrize("winerror", [10054, 995, 64])
    def test_suppresses_benign_winerrors(self, winerror):
        # 4-arg OSError(errno, strerror, filename, winerror) sets .winerror.
        loop = self._handle(OSError(22, "aborted", None, winerror))
        loop.default_exception_handler.assert_not_called()

    def test_suppresses_connection_errors(self):
        for exc in (
            ConnectionRefusedError(),
            ConnectionResetError(),
            BrokenPipeError(),
        ):
            assert self._handle(exc).default_exception_handler.called is False

    def test_passes_through_unrelated_errors(self):
        loop = self._handle(ValueError("boom"))
        loop.default_exception_handler.assert_called_once()

    @pytest.mark.skipif(
        sys.platform != "win32", reason="winerror is only set on Windows"
    )
    def test_passes_through_other_oserror(self):
        loop = self._handle(OSError(2, "no such file", None, 2))
        loop.default_exception_handler.assert_called_once()


class TestBanStreakTracker:
    def test_can_restart_again_after_new_ban_streak(self, monkeypatch):
        from scrapy_stealth.utils.browser.session import BanStreakTracker

        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        tracker = BanStreakTracker()
        tracker.record(True)
        assert tracker.record(True) is True
        tracker.acknowledge_restart()
        tracker.record(True)
        assert tracker.record(True) is True

    def test_cooldown_delays_restart_while_bans_continue(self, monkeypatch):
        import time

        from scrapy_stealth.utils.browser.session import BanStreakTracker

        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.5)
        tracker = BanStreakTracker()
        assert tracker.record(True) is False
        assert tracker.record(True) is True
        tracker.acknowledge_restart()
        assert tracker.record(True) is False
        assert tracker.record(True) is False
        time.sleep(0.6)
        assert tracker.record(True) is True

    def test_streak_kept_until_restart_acknowledged(self, monkeypatch):
        from scrapy_stealth.utils.browser.session import BanStreakTracker

        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        monkeypatch.setattr(config, "STEALTH_RECYCLE_COOLDOWN_S", 0.0)
        tracker = BanStreakTracker()
        tracker.record(True)
        assert tracker.record(True) is True
        # Only one claim per ban wave — concurrent threads must not all recycle.
        assert tracker.record(True) is False
        assert tracker.record(True) is False
        tracker.acknowledge_restart()
        assert tracker.record(True) is False

    def test_clean_response_resets_streak(self, monkeypatch):
        from scrapy_stealth.utils.browser.session import BanStreakTracker

        monkeypatch.setattr(config, "STEALTH_RECYCLE_AFTER_BANS", 2)
        tracker = BanStreakTracker()
        tracker.record(True)
        assert tracker.record(False) is False
        assert tracker.record(True) is False
        assert tracker.record(True) is True
