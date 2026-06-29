from __future__ import annotations

import asyncio
import base64
import contextlib
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import weakref
from typing import Any
from urllib.parse import urlparse

from .js_challenge import _JS_IS_CHALLENGE
from .logger import get_logger

logger = get_logger()


def _cleanup_browser_profiles(keep: str | None = None) -> int:
    """
    Delete stale ``uc_*`` temp profile directories left behind by nodriver.

    nodriver creates a fresh ``tempfile.mkdtemp(prefix="uc_")`` directory for
    every browser session and never removes it on exit, causing %TEMP% (Windows)
    or /tmp (Linux/macOS) to accumulate hundreds of MB over time.

    This function scans the system temp directory, removes every ``uc_*`` folder
    that is **not** currently in use, and returns the number of directories
    deleted.

    Parameters
    ----------
    keep:
        Absolute path of the profile directory that belongs to the *currently
        running* browser session.  If supplied, that directory is skipped so
        the live browser is never disrupted.  Pass ``browser.config.user_data_dir``
        (the nodriver config attribute) as this value.

    Returns
    -------
    int
        Number of directories successfully deleted.
    """
    tmp = tempfile.gettempdir()
    deleted = 0
    errors = 0

    try:
        entries = os.scandir(tmp)
    except OSError as exc:
        logger.debug("_cleanup_browser_profiles: cannot scan %s: %s", tmp, exc)
        return 0

    with entries:
        for entry in entries:
            if not (
                entry.name.startswith("uc_") and entry.is_dir(follow_symlinks=False)
            ):
                continue
            if keep and os.path.abspath(entry.path) == os.path.abspath(keep):
                continue
            try:
                shutil.rmtree(entry.path, ignore_errors=False)
                deleted += 1
                logger.debug("_cleanup_browser_profiles: removed %s", entry.path)
            except OSError as exc:
                # Directory is still locked by another Chrome process — skip it.
                errors += 1
                logger.debug(
                    "_cleanup_browser_profiles: could not remove %s: %s",
                    entry.path,
                    exc,
                )

    if deleted or errors:
        logger.debug(
            "_cleanup_browser_profiles: deleted=%d skipped_locked=%d",
            deleted,
            errors,
        )
    return deleted


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
_JS_CURRENT_URL = "window.location.href"
# Detects pages that are definitively blocked/errored with no content to wait
# for.  Akamai 403/429 pages have an empty or near-empty body and a title of
# "Access Denied", "403 Forbidden", "429 Too Many Requests", etc.  Matching on
# title is faster and more reliable than waiting for Navigation Timing to
# populate responseStatus when the connection is killed at the edge.
_JS_ERROR_TITLE = (
    "(() => {"
    "  const t = (document.title || '').toLowerCase();"
    "  return /access denied|forbidden|too many requests|blocked|error|unavailable/.test(t);"
    "})()"
)

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

    We deliberately do NOT cancel pending tasks inside this helper.  Callers
    must drain their own user-visible work first: ``_reset_browser`` drains
    every pending task via ``_drain_loop_tasks()`` and awaits the proxy relay
    via ``await_closed()`` before invoking ``_stop_loop``.
    What remains at loop-stop time is only nodriver-internal I/O, which does
    not need explicit cancellation.

    The ``InvalidStateError`` that surfaces on Windows (Python 3.13+) when
    WinError-995 I/O-abort callbacks fire against already-done Proactor futures
    during teardown is handled in ``_run_loop`` via a bare except.  Closing the
    loop *after* the thread has exited ensures no further callbacks can fire
    against the half-torn-down Proactor selector.
    """
    if loop is None:
        return
    try:
        loop.call_soon_threadsafe(loop.stop)
    except RuntimeError:
        pass
    if thread is not None:
        thread.join(timeout=timeout)
    # Close the loop after the thread has fully stopped.  A closed loop raises
    # RuntimeError on any further use, which is the correct and expected
    # behaviour — _reset_browser always replaces self._loop with a fresh one.
    if not loop.is_closed():
        try:
            loop.close()
        except Exception:
            pass


def _splash_url() -> str:
    # about:blank is the safest warmup target: Chrome loads it instantly,
    # it does not produce a Navigation Timing entry that could confuse
    # _wait_for_status, and it cannot be mis-returned by nodriver's
    # browser.get(url, new_tab=True) as an active tab.
    #
    # We previously used a file:// URI pointing at docs/static/logo.png, but
    # that caused two problems:
    #   1. Chrome opens the PNG in the main tab and leaves it "active".
    #      nodriver's get(url, new_tab=True) sometimes returns the main tab
    #      instead of the newly created tab — so _do_fetch ends up evaluating
    #      JS against logo.png instead of the target URL.
    #   2. A file:// PNG never writes a responseStatus to Navigation Timing,
    #      so _wait_for_status burns its full 8s timeout then falls back to
    #      200, leading to the same 28s-before-timeout problem we fixed for
    #      Akamai 403s.
    return "about:blank"


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

    Fast-path: if the page title already signals a definitive block/error
    (Akamai "Access Denied", generic 403/429 pages, etc.) we return 403
    immediately rather than waiting the full *timeout* for a Navigation Timing
    entry that will never arrive.  This prevents _do_fetch from entering
    _smart_wait and burning 20 more seconds on a page that has already
    delivered its final (empty) response.
    """

    async def _poll() -> int:
        while True:
            raw = await page.evaluate(_JS_STATUS)
            value = int(raw) if raw else 0
            if value != 0:
                return value
            # Fast-path: definitive block/error title means the response is
            # already final — no Navigation Timing entry will ever appear.
            if await page.evaluate(_JS_ERROR_TITLE):
                logger.debug(
                    "_wait_for_status: error title detected — returning 403 early"
                )
                return 403
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

    # If the page title already signals a block, there's nothing to wait for —
    # the body will never grow.  Return immediately so _do_fetch can collect
    # the (empty/error) HTML and let the ban tracker handle the response.
    if await page.evaluate(_JS_ERROR_TITLE):
        logger.debug("_smart_wait: blocked page title detected — skipping wait")
        return

    logger.debug(
        "_smart_wait: Challenge or script stub detected. Waiting for content to populate..."
    )

    last_len = body_len
    stalled_ticks = 0
    _STALL_LIMIT = 6  # 3 seconds of no body growth → give up

    async def _poll() -> None:
        nonlocal last_len, stalled_ticks
        while True:
            current_len = int(await page.evaluate(_JS_BODY_LEN))

            # Re-evaluate challenge status. If the script injected a new challenge UI
            # or if the body length has cleared the threshold, we keep moving.
            is_still_stub = await page.evaluate(
                "(() => { const b=document.body; return b && b.children.length === 1 && b.children[0].tagName === 'SCRIPT'; })()"
            )

            if current_len >= _CONTENT_SHORT_THRESHOLD and not is_still_stub:
                return

            # Bail early if the body has completely stopped growing — this means
            # the page delivered its final (blocked) response and is not going
            # to inject any content.  A real challenge page (Cloudflare, Akamai)
            # will grow the DOM as it runs JS; a hard block will stay flat.
            if current_len == last_len:
                stalled_ticks += 1
                if stalled_ticks >= _STALL_LIMIT:
                    logger.debug(
                        "_smart_wait: body stalled at %d chars for %.1fs — aborting",
                        current_len,
                        stalled_ticks * 0.5,
                    )
                    return
            else:
                stalled_ticks = 0
                last_len = current_len

            await asyncio.sleep(0.5)

    try:
        await asyncio.wait_for(_poll(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning("_smart_wait: timed out waiting for challenge to resolve")

    await asyncio.sleep(settle)


class ProxyRelay:
    """
    A local TCP relay that forwards every browser connection to the upstream
    proxy, injecting Proxy-Authorization on the way out.

    ``asyncio.start_server`` only closes the *accept* socket when
    ``server.close()`` is called — it does NOT cancel the already-accepted
    ``handle()`` tasks that are still mid-connection.  Those orphaned tasks
    are destroyed by Python's GC after the event loop closes, which triggers
    the "Task was destroyed but it is pending!" warning and, because their
    ``finally`` blocks call ``writer.close()`` against a closed loop, also
    "Exception ignored while closing generator: RuntimeError: Event loop is
    closed".

    This class wraps the server and tracks every live ``handle`` task in a
    ``WeakSet``.  ``close()`` cancels them all and waits for them to finish
    before returning, so the loop teardown that follows always finds an empty
    task set.
    """

    def __init__(self, server: asyncio.AbstractServer, port: int) -> None:
        self._server = server
        self.port = port
        self._tasks: weakref.WeakSet[asyncio.Task[None]] = weakref.WeakSet()

    def _track(self, task: asyncio.Task[None]) -> None:
        self._tasks.add(task)

    def close(self) -> None:
        """Stop accepting new connections (non-blocking; call await_closed next)."""
        self._server.close()

    async def await_closed(self) -> None:
        """Cancel all live handle tasks and wait for them to finish."""
        self._server.close()
        tasks = list(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        try:
            await self._server.wait_closed()
        except Exception:
            pass


def _close_writer(w: asyncio.StreamWriter) -> None:
    """
    Close *w* swallowing both OSError and RuntimeError.

    StreamWriter.close() → transport.close() → loop.call_soon(...).
    If the event loop is already closed that last call raises
    ``RuntimeError: Event loop is closed``, producing a noisy
    "Exception ignored while closing generator" traceback.
    We swallow both error types so teardown is always silent.
    """
    try:
        w.close()
    except (OSError, RuntimeError):
        pass


async def _start_proxy_relay(proxy_url: str) -> tuple[ProxyRelay, int]:
    """
    Start a local relay on 127.0.0.1 that forwards every connection to the
    upstream proxy, injecting the Proxy-Authorization header on the way out.

    Chrome/Brave honour a plain ``--proxy-server=127.0.0.1:<port>`` flag while
    the upstream credentials never touch the browser. Unlike extension- or
    CDP-based proxy auth (both flaky in nodriver), this also propagates into
    contexts created via ``browser.create_context()``.

    Returns ``(ProxyRelay, listen_port)``.  Call ``await relay.await_closed()``
    to cancel all live handle tasks and drain the server cleanly.
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

    # Forward-declare so handle() can call relay._track() on itself.
    relay_holder: list[ProxyRelay] = []

    async def handle(
        client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
    ) -> None:
        # Register this task so ProxyRelay.await_closed() can cancel it.
        current = asyncio.current_task()
        if current is not None and relay_holder:
            relay_holder[0]._track(current)

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
                except (OSError, asyncio.CancelledError):
                    pass
                finally:
                    _close_writer(writer)

            await asyncio.gather(
                pipe(upstream_reader, client_writer),
                pipe(client_reader, upstream_writer),
                return_exceptions=True,
            )
        except (OSError, asyncio.CancelledError):
            pass
        finally:
            for w in (client_writer, upstream_writer):
                if w is not None:
                    _close_writer(w)

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    listen_port = server.sockets[0].getsockname()[1]
    relay = ProxyRelay(server, listen_port)
    relay_holder.append(relay)
    return relay, listen_port


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
