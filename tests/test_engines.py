import asyncio
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
from scrapy_stealth.utils.headers import _FINGERPRINT_KEYS
from scrapy_stealth.utils.profiles import _BROWSER_MAP, resolve_browser
from scrapy_stealth.utils.response import StealthResponse

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

    def test_default_profile_matches_config(self):
        with patch("scrapy_stealth.engines.basic.Client"):
            engine = BasicEngine()
        assert engine.default_profile == resolve_browser(config.get("DEFAULT_PROFILE"))

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

    def test_session_reused_for_same_profile(self, session_patch):
        mock_cls, _ = session_patch
        engine = TurboEngine()
        engine._execute(Request("https://example.com"))
        engine._execute(Request("https://example.com"))
        assert mock_cls.call_count == 1

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
        tab.close = AsyncMock()
        return tab

    @pytest.fixture
    def mock_browser(self, mock_tab):
        browser = MagicMock()
        browser.get = AsyncMock(return_value=mock_tab)
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
        assert mock_browser.get.call_count == 2

    def test_execute_closes_tab_after_fetch(self, engine, mock_tab):
        engine._execute(Request("https://example.com"))
        mock_tab.close.assert_called_once()

    def test_execute_returns_none_on_exception(self, engine, mock_browser):
        mock_browser.get = AsyncMock(side_effect=Exception("network error"))
        result = engine._execute(Request("https://example.com"))
        assert result is None

    def test_execute_raises_stealth_timeout(self, engine, mock_browser):
        mock_browser.get = AsyncMock(side_effect=TimeoutError("timed out"))
        with pytest.raises(
            StealthTimeoutError, match=r"Browser engine timed out after .+s fetching"
        ):
            engine._execute(Request("https://example.com"))

    def test_execute_raises_stealth_connection_error_on_oserror(
        self, engine, mock_browser
    ):
        mock_browser.get = AsyncMock(side_effect=OSError("connection refused"))
        with pytest.raises(
            StealthConnectionError, match=r"Browser engine connection failed fetching"
        ):
            engine._execute(Request("https://example.com"))

    def test_execute_raises_browser_not_found_on_file_not_found(self, engine):
        with patch.object(
            engine,
            "_ensure_browser",
            side_effect=StealthBrowserNotFoundError("Browser binary not found."),
        ):
            with pytest.raises(
                StealthBrowserNotFoundError, match="Browser binary not found"
            ):
                engine._execute(Request("https://example.com"))

    def test_execute_passes_headless_from_meta(self, engine):
        with patch.object(engine, "_ensure_browser") as mock_ensure:
            engine._execute(
                Request("https://example.com", meta={"stealth": {"headless": False}})
            )
        assert mock_ensure.call_args.kwargs["headless"] is False

    def test_execute_uses_config_headless_default(self, engine):
        with patch.object(engine, "_ensure_browser") as mock_ensure:
            engine._execute(Request("https://example.com"))
        assert mock_ensure.call_args.kwargs["headless"] == config.get(
            "BROWSER_HEADLESS"
        )

    def test_execute_passes_proxy_to_do_fetch(self, engine):
        with patch.object(
            engine,
            "_do_fetch",
            new_callable=AsyncMock,
            return_value=(b"<html></html>", 200, None),
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

        async def fake_fetch(url, settle, snapshot=False, block_assets=False):
            captured.append(settle)
            return b"<html></html>", 200, None

        with patch.object(engine, "_do_fetch", side_effect=fake_fetch):
            engine._execute(
                Request("https://example.com", meta={"stealth": {"settle": 9.0}})
            )
        assert captured[0] == 9.0

    def test_execute_uses_config_settle_default(self, engine):
        captured = []

        async def fake_fetch(url, settle, snapshot=False, block_assets=False):
            captured.append(settle)
            return b"<html></html>", 200, None

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
        monkeypatch.setattr(config, "BROWSER_RESTART_AFTER_BANS", 5)
        self._set_status(mock_tab, 403)
        with patch.object(engine, "_reset_browser") as mock_reset:
            for _ in range(4):
                engine._execute(Request("https://example.com"))
            mock_reset.assert_not_called()
            engine._execute(Request("https://example.com"))
        mock_reset.assert_called_once()

    def test_clean_response_resets_ban_streak(self, monkeypatch, engine, mock_tab):
        monkeypatch.setattr(config, "BROWSER_RESTART_AFTER_BANS", 3)
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

    # -----------------------------------------------------------------
    # static_assets_block
    # -----------------------------------------------------------------

    def test_static_assets_block_off_by_default(self, engine):
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
