from __future__ import annotations

import asyncio
import base64
import contextlib
import os
import random
import subprocess
import sys
import threading
import time
from typing import Any
from urllib.parse import urlparse

from .js_challenge import _JS_IS_CHALLENGE
from .logger import get_logger

logger = get_logger()

_BROWSER_ARGS: list[str] = [
    "--window-position=0,0",
    "--disable-blink-features=AutomationControlled",
]

_FP_WINDOW_SIZES: list[str] = [
    "1366,768",
    "1440,900",
    "1536,864",
    "1600,900",
    "1920,1080",
    "1280,800",
    "1280,1024",
    "1360,768",
]

_FP_LANGUAGES: list[str] = [
    "en-GB,en;q=0.9",
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,en-GB;q=0.8",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.8",
    "en-AU,en;q=0.9",
    "en-CA,en;q=0.9",
]

_JS_HTML = "document.querySelector('.json-formatter-container') ? document.body.innerText : document.documentElement.innerHTML"
_JS_STATUS = "performance.getEntriesByType('navigation')[0]?.responseStatus ?? 0"
_JS_IS_CHROME_ERROR = "window.location.href.startsWith('chrome-error://')"
_JS_BODY_LEN = "document.body ? document.body.innerText.trim().length : 0"

# Resource types blocked when static_assets_block=True — covers images, fonts,
# stylesheets, and other media that aren't needed to read or detect-bypass a page.
_STATIC_ASSET_RESOURCE_TYPES: tuple[str, ...] = (
    "Image",
    "Font",
    "Stylesheet",
    "Media",
)

_CONTENT_SHORT_THRESHOLD = 2500

_xvfb_proc: Any = None  # module-level so only one Xvfb is started per process


def _random_fingerprint_args() -> list[str]:
    """
    Return Chrome launch args that vary per browser startup to present a
    distinct fingerprint on each session.

    All args are appended after ``_BROWSER_ARGS`` by
    ``BrowserEngine._build_args()`` so they always win over base defaults.
    Called once per ``_start()`` / ``_reset_browser()`` so each browser
    lifetime gets a stable but unique identity.
    """
    size = random.choice(_FP_WINDOW_SIZES)
    lang = random.choice(_FP_LANGUAGES)
    logger.debug("Browser fingerprint — size=%s  lang=%s", size, lang)
    return [
        f"--window-size={size}",
        f"--lang={lang}",
    ]


def _make_loop() -> asyncio.AbstractEventLoop:
    # ProactorEventLoop is required on Windows for Chrome subprocess management.
    if sys.platform == "win32":
        return asyncio.ProactorEventLoop()
    return asyncio.new_event_loop()


def _stop_loop(
    loop: asyncio.AbstractEventLoop | None,
    thread: threading.Thread | None,
    timeout: float = 5.0,
) -> None:
    """
    Stop *loop* and join *thread*, waiting for the loop to actually finish
    running before returning.

    Discarding a running loop/thread pair without joining lets the old thread
    keep polling the (Proactor, on Windows) selector after the new loop/thread
    has already started — in-flight I/O gets aborted mid-callback and raises
    into a thread nobody is watching, surfacing as unretrieved task exceptions
    or an ``InvalidStateError`` crash. Joining first eliminates that overlap.

    On Windows with ProactorEventLoop, stopping the loop while overlapped I/O
    ops (proxy-relay accept, tab pipes) are still in-flight causes Windows to
    cancel them with WinError 995.  The cancellation callback fires inside
    ``_poll`` and calls ``future.set_exception()`` on a future that the loop
    already transitioned to a done/cancelled state, raising
    ``InvalidStateError`` directly in the thread — bypassing the loop's own
    exception handler.  We prevent this by scheduling a coroutine that cancels
    all pending tasks first, giving them a chance to clean up their futures
    before the loop actually stops.
    """
    if loop is None:
        return

    async def _cancel_all_tasks() -> None:
        tasks = [t for t in asyncio.all_tasks(loop) if not t.done()]
        for task in tasks:
            task.cancel()
        if tasks:
            # Let the cancellation callbacks run so futures reach a terminal
            # state before the Proactor's completion port is torn down.
            await asyncio.gather(*tasks, return_exceptions=True)

    try:
        future = asyncio.run_coroutine_threadsafe(_cancel_all_tasks(), loop)
        future.result(timeout=max(timeout - 1.0, 1.0))
    except Exception:
        pass

    try:
        loop.call_soon_threadsafe(loop.stop)
    except RuntimeError:
        pass

    if thread is not None:
        thread.join(timeout=timeout)

    # Close the loop after the thread has exited so no callbacks can fire
    # against a half-torn-down Proactor selector.  A closed loop raises
    # RuntimeError on any further use, which is the correct behaviour.
    if not loop.is_closed():
        try:
            loop.close()
        except Exception:
            pass


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


@contextlib.asynccontextmanager
async def _block_static_assets(page: Any):
    """
    While active, fail every request whose resource type is in
    ``_STATIC_ASSET_RESOURCE_TYPES`` (images, fonts, CSS, media) via the CDP
    Fetch domain — everything else (document, script, XHR/fetch) passes
    through untouched. Scoped to *page* and torn down on exit so it never
    leaks to the next tab.
    """
    import nodriver.cdp.fetch as _cdp_fetch
    import nodriver.cdp.network as _cdp_network

    async def _on_paused(event: _cdp_fetch.RequestPaused, *_: Any) -> None:
        try:
            if event.resource_type.value in _STATIC_ASSET_RESOURCE_TYPES:
                await page.send(
                    _cdp_fetch.fail_request(
                        event.request_id, _cdp_network.ErrorReason.BLOCKED_BY_CLIENT
                    )
                )
            else:
                await page.send(_cdp_fetch.continue_request(event.request_id))
        except Exception:
            pass

    await page.send(_cdp_fetch.enable())
    page.add_handler(_cdp_fetch.RequestPaused, _on_paused)
    try:
        yield
    finally:
        page.remove_handler(_cdp_fetch.RequestPaused, _on_paused)
        try:
            await page.send(_cdp_fetch.disable())
        except Exception:
            pass


def _proxy_bypass_args(bypass_list: Any) -> list[str]:
    """
    Build the Chrome ``--proxy-bypass-list`` launch flag from a user-supplied
    list of domains/patterns.

    Each entry is sent to Chrome verbatim (only surrounding whitespace is
    trimmed and empties dropped), so the full Chrome bypass syntax is supported
    — bare hostnames, wildcards (``*.example.com``), IP/CIDR ranges, ports, and
    the special ``<local>`` token. Entries are joined with ``;`` as Chrome
    expects. Returns ``[]`` when the list is empty, so callers can splat the
    result unconditionally::

        _proxy_bypass_args(["example.com", "*.internal", "<local>"])
        -> ["--proxy-bypass-list=example.com;*.internal;<local>"]
    """
    if not bypass_list:
        return []
    entries = [str(e).strip() for e in bypass_list if e and str(e).strip()]
    if not entries:
        return []
    return [f"--proxy-bypass-list={';'.join(entries)}"]


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


async def _wait_for_status(page: Any, timeout: float = 8.0) -> int:
    """
    Poll ``performance.getEntriesByType('navigation')[0].responseStatus`` until
    it returns a non-zero value, then return it.

    Background
    ----------
    Chrome writes the Navigation Timing entry asynchronously — it can still be
    absent (empty array) or carry ``responseStatus: 0`` immediately after
    ``page.wait()`` returns, particularly when a proxy is in use or the page
    involved one or more redirects.  Returning ``0`` from this function would
    cause the caller to mis-classify every response as a success (``200 <= 0``
    is False, so the wait-for-content step would be skipped on pages that
    actually loaded fine).

    The fallback of ``200`` is intentional: if Chrome never exposes a status
    within *timeout* seconds (e.g. the page is a pure client-side SPA that
    replaces the navigation entry), treating it as success is the safest
    assumption — the caller will still wait for content as normal.
    """

    async def _poll() -> int:
        while True:
            raw = await page.evaluate(_JS_STATUS)
            value = int(raw) if raw else 0
            if value != 0:
                return value
            await asyncio.sleep(0.25)

    try:
        return await asyncio.wait_for(_poll(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.debug(
            "_wait_for_status timed out after %.1fs — defaulting to 200", timeout
        )
        return 200


async def _smart_wait(page: Any, settle: float, timeout: float = 20.0) -> None:
    """
    Intelligently wait for page content to load, skipping the wait entirely
    when the page is already fully rendered, but robustly catching anti-bot stubs.
    """
    # Safeguard: wait a split second for the initial DOM frame to touch down
    await asyncio.sleep(0.2)

    body_len = int(await page.evaluate(_JS_BODY_LEN))

    if body_len >= _CONTENT_SHORT_THRESHOLD:
        return

    if not bool(await page.evaluate(_JS_IS_CHALLENGE)):
        return

    logger.debug(
        "_smart_wait: Challenge or script stub detected. Waiting for content to populate..."
    )

    async def _poll() -> None:
        while True:
            current_len = int(await page.evaluate(_JS_BODY_LEN))

            # Re-evaluate challenge status. If the script injected a new challenge UI
            # or if the body length has cleared the threshold, we keep moving.
            is_still_stub = await page.evaluate(
                "(() => { const b=document.body; return b && b.children.length === 1 && b.children[0].tagName === 'SCRIPT'; })()"
            )

            if current_len >= _CONTENT_SHORT_THRESHOLD and not is_still_stub:
                return
            await asyncio.sleep(0.5)

    try:
        await asyncio.wait_for(_poll(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("_smart_wait: timed out waiting for challenge to resolve")

    await asyncio.sleep(settle)


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


class BanStreakTracker:
    """
    Counts *consecutive* banned/challenged responses and signals a restart once
    the streak reaches ``BROWSER_RESTART_AFTER_BANS``. Any clean response resets
    the streak to zero, so a browser sailing through cleanly is never restarted.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._streak = 0

    def record(self, banned: bool) -> bool:
        """Record one outcome; returns True if the browser should restart."""
        from ..config import config

        with self._lock:
            if not banned:
                self._streak = 0
                return False
            self._streak += 1
            if self._streak >= config.get("BROWSER_RESTART_AFTER_BANS"):
                self._streak = 0
                return True
            return False
