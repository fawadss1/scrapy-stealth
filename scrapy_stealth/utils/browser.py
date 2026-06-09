from __future__ import annotations

import asyncio
import base64
import os
import subprocess
import sys
import time
from typing import Any
from urllib.parse import urlparse

from ..utils.logger import get_logger

logger = get_logger()

_BROWSER_ARGS: list[str] = [
    "--window-size=1366,768",
    "--window-position=0,0",
    "--disable-blink-features=AutomationControlled",
]
_JS_HTML = "document.querySelector('.json-formatter-container') ? document.body.innerText : document.documentElement.innerHTML"
_JS_STATUS = "performance.getEntriesByType('navigation')[0]?.responseStatus ?? 200"
_JS_IS_CHROME_ERROR = "window.location.href.startsWith('chrome-error://')"
_JS_BODY_LEN = "document.body ? document.body.innerText.trim().length : 0"
_xvfb_proc: Any = None  # module-level so only one Xvfb is started per process


def _make_loop() -> asyncio.AbstractEventLoop:
    # ProactorEventLoop is required on Windows for Chrome subprocess management.
    if sys.platform == "win32":
        return asyncio.ProactorEventLoop()
    return asyncio.new_event_loop()


def _splash_url() -> str:
    import json
    import pathlib

    try:
        from importlib.metadata import distribution

        raw = distribution("scrapy-stealth").read_text("direct_url.json")
        if raw:
            url = json.loads(raw).get("url", "")
            if url.startswith("file:"):
                source = pathlib.Path.from_uri(url)
                if source.suffix == ".whl":
                    source = source.parent.parent
                logo = source / "docs" / "static" / "logo.png"
                if logo.exists():
                    return logo.as_uri()
    except Exception:
        pass
    return "chrome://welcome"


async def _cdp_snapshot(page: Any) -> bytes | None:
    """Take a screenshot of the page using Chrome DevTools Protocol. Returns the raw PNG bytes, or None on failure."""
    try:
        import nodriver.cdp.page as _cdp_page

        data: str = await page.send(_cdp_page.capture_screenshot())
        return base64.b64decode(data)
    except Exception:
        return None


def _silence_browser() -> None:
    import logging

    import nodriver.core.util as _nd_util

    logging.getLogger("nodriver").setLevel(logging.WARNING)
    logging.getLogger("nodriver.core.util").setLevel(logging.CRITICAL)
    _nd_util.print = lambda *a, **kw: None


def _is_browser_crash(exc: BaseException) -> bool:
    return isinstance(exc, ConnectionRefusedError)


def _ensure_xvfb(headless: bool = False) -> None:
    """Enforce a display when running non-headless.

    When ``headless`` is True the browser needs no display, so this is a no-op.
    When ``headless`` is False a display is required: the real desktop on Windows
    or an existing DISPLAY, otherwise an Xvfb virtual display is started — with no
    fallback to headless. If Xvfb is not installed we raise, so the browser is
    never silently downgraded to (easily detectable) headless mode.
    """

    global _xvfb_proc
    if headless:
        return
    if sys.platform == "win32" or os.environ.get("DISPLAY"):
        return
    if _xvfb_proc is not None:
        return  # already started
    try:
        _xvfb_proc = subprocess.Popen(
            ["Xvfb", ":99", "-screen", "0", "1366x768x24", "-ac"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Xvfb is required to run the browser non-headless but was not found. "
            "Install it with: apt-get install -y xvfb"
        ) from exc
    os.environ["DISPLAY"] = ":99"
    # Wait until Xvfb's Unix socket appears (up to 5 seconds) before Chrome connects.
    for _ in range(50):
        if os.path.exists("/tmp/.X11-unix/X99"):
            break
        time.sleep(0.1)
    logger.debug("Xvfb started on :99 — browser will run non-headless")


async def _wait_for_content(page: Any, timeout: float = 10.0) -> None:
    """Poll until visible body text is substantial; silently continue on timeout."""

    async def _poll() -> None:
        while True:
            if int(await page.evaluate(_JS_BODY_LEN)) > 2500:
                return
            await asyncio.sleep(0.5)

    try:
        await asyncio.wait_for(_poll(), timeout=timeout)
    except asyncio.TimeoutError:
        pass


async def _start_proxy_relay(proxy_url: str) -> tuple[asyncio.AbstractServer, int]:
    """
    Start a local relay on 127.0.0.1 that forwards every connection to the
    upstream proxy, injecting the Proxy-Authorization header on the way out.

    Chrome/Brave honour a plain ``--proxy-server=127.0.0.1:<port>`` flag while
    the upstream credentials never touch the browser. Unlike extension- or
    CDP-based proxy auth (both flaky in nodriver), this also propagates into
    contexts created via ``browser.create_context()``.

    Returns ``(server, listen_port)``. Close the server to tear the relay down.
    """
    parsed = urlparse(proxy_url if "://" in proxy_url else f"http://{proxy_url}")
    host = parsed.hostname
    port = parsed.port or 3128
    auth_header = b""
    if parsed.username:
        token = base64.b64encode(
            f"{parsed.username}:{parsed.password or ''}".encode()
        ).decode()
        auth_header = b"Proxy-Authorization: Basic " + token.encode() + b"\r\n"

    async def handle(
        client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
    ) -> None:
        upstream_writer: asyncio.StreamWriter | None = None
        try:
            # Read the client's request head (CONNECT or absolute-URI request).
            header = b""
            while b"\r\n\r\n" not in header:
                chunk = await client_reader.read(65536)
                if not chunk:
                    return
                header += chunk

            upstream_reader, upstream_writer = await asyncio.open_connection(host, port)

            # Inject credentials right after the request line, then forward.
            request_line, _, rest = header.partition(b"\r\n")
            upstream_writer.write(request_line + b"\r\n" + auth_header + rest)
            await upstream_writer.drain()

            async def pipe(
                reader: asyncio.StreamReader, writer: asyncio.StreamWriter
            ) -> None:
                try:
                    while True:
                        data = await reader.read(65536)
                        if not data:
                            break
                        writer.write(data)
                        await writer.drain()
                except OSError:
                    pass
                finally:
                    try:
                        writer.close()
                    except OSError:
                        pass

            await asyncio.gather(
                pipe(upstream_reader, client_writer),
                pipe(client_reader, upstream_writer),
            )
        except OSError:
            pass
        finally:
            for w in (client_writer, upstream_writer):
                if w is not None:
                    try:
                        w.close()
                    except OSError:
                        pass

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    listen_port = server.sockets[0].getsockname()[1]
    return server, listen_port
