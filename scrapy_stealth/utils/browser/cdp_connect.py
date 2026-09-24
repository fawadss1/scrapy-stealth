from __future__ import annotations

import asyncio
import json
import logging
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, NoReturn

from ...exceptions import (
    StealthCdpConnectionError,
    StealthConnectionError,
    raise_stealth,
)

logger = logging.getLogger(__name__)


def merge_cdp_connect_kwargs(
    base: dict[str, Any] | None, override: dict[str, Any] | None
) -> dict[str, Any]:
    """Merge global and per-request CDP connect options (override wins)."""
    merged: dict[str, Any] = dict(base or {})
    if override:
        extra = dict(override)
        base_headers = dict(merged.get("headers") or {})
        override_headers = dict(extra.pop("headers", {}) or {})
        merged.update(extra)
        if base_headers or override_headers:
            merged["headers"] = {**base_headers, **override_headers}
    return merged


def _normalize_headers(headers: Any) -> dict[str, str]:
    if not headers:
        return {}
    if isinstance(headers, dict):
        return {str(k): str(v) for k, v in headers.items()}
    raise TypeError("cdp_connect_kwargs['headers'] must be a dict")


async def _fetch_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
    verify_ssl: bool = True,
) -> dict[str, Any]:
    def _request() -> dict[str, Any]:
        req = urllib.request.Request(url)
        for key, value in (headers or {}).items():
            req.add_header(key, value)
        context = None
        if not verify_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        try:
            with urllib.request.urlopen(
                req, timeout=timeout, context=context
            ) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:500]
            raise StealthConnectionError(
                f"CDP HTTP {exc.code} for {url!r}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise StealthConnectionError(
                f"CDP request failed for {url!r}: {exc.reason}"
            ) from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StealthConnectionError(
                f"CDP endpoint returned non-JSON from {url!r}"
            ) from exc
        if not isinstance(data, dict):
            raise StealthConnectionError(
                f"CDP endpoint returned unexpected JSON from {url!r}"
            )
        return data

    return await asyncio.get_running_loop().run_in_executor(None, _request)


def _version_url(base: str) -> str:
    return urllib.parse.urljoin(base.rstrip("/") + "/", "json/version")


def _short_cdp_detail(detail: str | None) -> str:
    if not detail:
        return "connection refused"
    text = detail.strip()
    if text.startswith("CDP request failed for "):
        _, _, text = text.partition(": ")
    if len(text) > 100:
        text = text[:97] + "..."
    return text


def format_cdp_unreachable(cdp_url: str, detail: str | None = None) -> str:
    """Short exception message when ``STEALTH_CDP_URL`` cannot be reached."""
    reason = _short_cdp_detail(detail)
    return (
        f"CDP browser not reachable at {cdp_url.strip()!r} ({reason}). "
        "Start Chromium with --remote-debugging-port or unset STEALTH_CDP_URL."
    )


def raise_cdp_unreachable(cdp_url: str, detail: str | None = None) -> NoReturn:
    url = cdp_url.strip()
    parsed = urllib.parse.urlparse(url)
    port = parsed.port or 9222
    logger.debug(
        "CDP unreachable at %s — start e.g. "
        'brave.exe --remote-debugging-port=%s --user-data-dir="%%LOCALAPPDATA%%\\scrapy-stealth-cdp" '
        "then check http://127.0.0.1:%s/json/version",
        url,
        port,
        port,
    )
    raise StealthCdpConnectionError(
        format_cdp_unreachable(cdp_url, detail),
        cdp_url=url,
    ) from None


def is_nodriver_connect_failure(exc: BaseException) -> bool:
    """True for nodriver's generic attach failure (often misleads on Windows)."""
    return "Failed to connect to browser" in str(exc)


def _classify_cdp_url(cdp_url: str) -> tuple[str, urllib.parse.ParseResult]:
    parsed = urllib.parse.urlparse(cdp_url.strip())
    if parsed.scheme in {"ws", "wss"}:
        return "websocket", parsed
    if parsed.scheme not in {"http", "https"}:
        raise_stealth(
            StealthConnectionError,
            f"Unsupported CDP URL scheme {parsed.scheme!r} in {cdp_url!r}. "
            "Use http(s)://… or ws(s)://…",
        )
    path = parsed.path or ""
    if path in {"", "/"}:
        return "debug_port", parsed
    return "http_base", parsed


async def _open_websocket(
    browser: Any, ws_url: str, headers: dict[str, str] | None
) -> None:
    import websockets
    from nodriver.core.connection import MAX_SIZE, PING_TIMEOUT

    header_list = list((headers or {}).items()) or None
    browser.websocket_url = ws_url
    if browser.socket and not browser.socket.close_code:
        return
    browser.socket = await websockets.connect(
        ws_url,
        ping_timeout=PING_TIMEOUT,
        max_size=MAX_SIZE,
        additional_headers=header_list,
    )
    browser._listener_task = asyncio.create_task(browser._listener())


async def _finish_browser_attach(browser: Any) -> Any:
    from nodriver.core import util

    util.get_registered_instances().add(browser)
    await browser.attach()
    await browser.update_targets()
    return browser


async def connect_cdp_browser(
    cdp_url: str, connect_kwargs: dict[str, Any] | None = None
) -> tuple[Any, bool]:
    """Connect to an external Chrome/Fortress CDP endpoint via nodriver.

    Returns ``(browser, owns_process)``. ``owns_process`` is always ``False``.
    """
    import nodriver as nd

    kwargs = dict(connect_kwargs or {})
    headers = _normalize_headers(kwargs.get("headers"))
    timeout = float(kwargs.get("timeout", 10.0))
    verify_ssl = bool(kwargs.get("verify_ssl", True))

    kind, parsed = _classify_cdp_url(cdp_url)

    if kind == "debug_port":
        host = parsed.hostname
        if not host:
            raise_stealth(StealthConnectionError, f"Invalid CDP URL: {cdp_url!r}")
        port = parsed.port or 9222
        scheme = parsed.scheme or "http"
        version_url = f"{scheme}://{host}:{port}/json/version"
        logger.debug("Connecting to local CDP debug port %s:%s", host, port)
        try:
            await _fetch_json(
                version_url,
                headers=headers,
                timeout=timeout,
                verify_ssl=verify_ssl,
            )
        except StealthConnectionError as exc:
            raise_cdp_unreachable(cdp_url, str(exc))
        try:
            browser = await nd.start(host=host, port=port)
        except Exception as exc:
            if is_nodriver_connect_failure(exc):
                raise_cdp_unreachable(cdp_url)
            raise_cdp_unreachable(cdp_url, str(exc))
        return browser, False

    if kind == "websocket":
        ws_url = cdp_url.strip()
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        config = nd.Config(host=host, port=port)
        browser = nd.Browser(config)
        browser._process = None
        browser._process_pid = None
        try:
            await _open_websocket(browser, ws_url, headers)
            browser = await _finish_browser_attach(browser)
        except StealthConnectionError as exc:
            raise_cdp_unreachable(cdp_url, str(exc))
        except Exception as exc:
            raise_cdp_unreachable(cdp_url, str(exc))
        return browser, False

    base = cdp_url.strip().rstrip("/")
    info = await _fetch_json(
        _version_url(base),
        headers=headers,
        timeout=timeout,
        verify_ssl=verify_ssl,
    )
    ws_url_raw = info.get("webSocketDebuggerUrl")
    if not isinstance(ws_url_raw, str) or not ws_url_raw:
        raise_stealth(
            StealthConnectionError,
            f"CDP /json/version at {base!r} did not include webSocketDebuggerUrl",
        )
    ws_url = ws_url_raw

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    config = nd.Config(host=host, port=port)
    browser = nd.Browser(config)
    browser._process = None
    browser._process_pid = None
    from nodriver.core._contradict import ContraDict

    browser.info = ContraDict(info, silent=True)

    try:
        await _open_websocket(browser, ws_url, headers)
        browser = await _finish_browser_attach(browser)
    except StealthConnectionError as exc:
        raise_cdp_unreachable(cdp_url, str(exc))
    except Exception as exc:
        raise_cdp_unreachable(cdp_url, str(exc))
    return browser, False
