from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from scrapy.http import Request

from scrapy_stealth.config import config
from scrapy_stealth.exceptions import StealthCdpConnectionError
from scrapy_stealth.utils.browser.cdp_connect import (
    _classify_cdp_url,
    _version_url,
    connect_cdp_browser,
    format_cdp_unreachable,
    merge_cdp_connect_kwargs,
)
from scrapy_stealth.utils.core.meta import resolve_cdp_connect_kwargs, resolve_cdp_url


class TestCdpUrlHelpers:
    def test_classify_debug_port(self):
        kind, parsed = _classify_cdp_url("http://127.0.0.1:9222")
        assert kind == "debug_port"
        assert parsed.port == 9222

    def test_classify_http_base(self):
        kind, _ = _classify_cdp_url("https://cdp.example.com/v1")
        assert kind == "http_base"

    def test_classify_ws_root_as_debug_port(self):
        for url in ("ws://localhost:9222", "ws://localhost:9222/", "wss://host:9222/"):
            kind, parsed = _classify_cdp_url(url)
            assert kind == "debug_port", url
            assert parsed.port == 9222 or url.startswith("wss://host")

    def test_classify_websocket_with_path(self):
        kind, _ = _classify_cdp_url(
            "ws://localhost:9222/devtools/browser/a902c456-4965-42ad-bf90-1fc929306eab"
        )
        assert kind == "websocket"
        kind, _ = _classify_cdp_url("wss://cdp.example.com/devtools/page/abc")
        assert kind == "websocket"

    def test_version_url(self):
        assert _version_url("https://host/cdp") == "https://host/cdp/json/version"

    def test_merge_connect_kwargs_headers(self):
        merged = merge_cdp_connect_kwargs(
            {"headers": {"Authorization": "Basic a"}, "timeout": 5},
            {"headers": {"X-Api-Key": "k"}, "verify_ssl": False},
        )
        assert merged["timeout"] == 5
        assert merged["verify_ssl"] is False
        assert merged["headers"] == {
            "Authorization": "Basic a",
            "X-Api-Key": "k",
        }


class TestMetaCdpResolve:
    def test_resolve_cdp_url_meta_override(self, monkeypatch):
        monkeypatch.setattr(config, "STEALTH_CDP_URL", "http://127.0.0.1:9222")
        req = Request(
            "https://example.com", meta={"stealth": {"cdp_url": "http://10.0.0.2:9222"}}
        )
        assert resolve_cdp_url(req) == "http://10.0.0.2:9222"

    def test_resolve_cdp_connect_kwargs_merge(self, monkeypatch):
        monkeypatch.setattr(
            config,
            "STEALTH_CDP_CONNECT_KWARGS",
            {"headers": {"Authorization": "Basic x"}},
        )
        req = Request(
            "https://example.com",
            meta={"stealth": {"cdp_connect_kwargs": {"timeout": 20}}},
        )
        kw = resolve_cdp_connect_kwargs(req)
        assert kw["timeout"] == 20
        assert kw["headers"]["Authorization"] == "Basic x"


def test_format_cdp_unreachable_ws_suggests_http():
    msg = format_cdp_unreachable("ws://127.0.0.1:9222/devtools/browser/x", "HTTP 404")
    assert "ws://127.0.0.1:9222/" in msg or "http://127.0.0.1:9222" in msg


@pytest.mark.asyncio
async def test_connect_ws_root_uses_debug_port():
    fake_browser = MagicMock()
    with (
        patch(
            "scrapy_stealth.utils.browser.cdp_connect._fetch_json",
            new_callable=AsyncMock,
            return_value={
                "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/x"
            },
        ),
        patch(
            "nodriver.start", new_callable=AsyncMock, return_value=fake_browser
        ) as start,
    ):
        browser, owns = await connect_cdp_browser("ws://localhost:9222/")
    start.assert_awaited_once_with(host="localhost", port=9222)
    assert owns is False


@pytest.mark.asyncio
async def test_connect_debug_port_uses_nodriver_start():
    fake_browser = MagicMock()
    with (
        patch(
            "scrapy_stealth.utils.browser.cdp_connect._fetch_json",
            new_callable=AsyncMock,
            return_value={
                "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/x"
            },
        ),
        patch(
            "nodriver.start", new_callable=AsyncMock, return_value=fake_browser
        ) as start,
    ):
        browser, owns = await connect_cdp_browser("http://127.0.0.1:9222")
    start.assert_awaited_once_with(host="127.0.0.1", port=9222)
    assert browser is fake_browser
    assert owns is False


def test_format_cdp_unreachable_is_compact():
    msg = format_cdp_unreachable("http://127.0.0.1:9222", "connection refused")
    assert "127.0.0.1:9222" in msg
    assert "connection refused" in msg
    assert "STEALTH_CDP_URL" in msg
    assert msg.count("\n") == 0


@pytest.mark.asyncio
async def test_debug_port_unreachable_raises_stealth_cdp_connection_error():
    with pytest.raises(StealthCdpConnectionError) as exc_info:
        await connect_cdp_browser("http://127.0.0.1:59998")
    exc = exc_info.value
    assert exc.cdp_url == "http://127.0.0.1:59998"
    msg = str(exc)
    assert "CDP browser not reachable" in msg
    assert "59998" in msg


@pytest.mark.asyncio
async def test_connect_http_base_fetches_version_and_attaches():
    version = {"webSocketDebuggerUrl": "wss://remote.example/ws"}
    fake_browser = MagicMock()
    fake_browser._process = None
    fake_browser._process_pid = None
    fake_browser.socket = MagicMock()
    fake_browser.socket.close_code = None
    fake_browser.attach = AsyncMock()
    fake_browser.update_targets = AsyncMock()
    fake_browser._listener = MagicMock(return_value=AsyncMock())

    with (
        patch(
            "scrapy_stealth.utils.browser.cdp_connect._fetch_json",
            new_callable=AsyncMock,
            return_value=version,
        ) as fetch,
        patch("nodriver.Browser", return_value=fake_browser),
        patch("nodriver.Config"),
        patch(
            "scrapy_stealth.utils.browser.cdp_connect._open_websocket",
            new_callable=AsyncMock,
        ),
        patch(
            "scrapy_stealth.utils.browser.cdp_connect._finish_browser_attach",
            new_callable=AsyncMock,
            return_value=fake_browser,
        ),
    ):
        browser, owns = await connect_cdp_browser(
            "https://remote.example/cdp",
            {"headers": {"Authorization": "Basic token"}},
        )

    fetch.assert_awaited_once()
    assert fetch.await_args.kwargs["headers"]["Authorization"] == "Basic token"
    assert browser is fake_browser
    assert owns is False
