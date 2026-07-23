from __future__ import annotations

import asyncio
import base64
import contextlib
import ipaddress
import os
import random
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import weakref
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .js_challenge import _JS_IS_CHALLENGE
from .logger import get_logger

logger = get_logger()


def _cleanup_browser_profiles(keep: str | None = None) -> int:
    """Delete stale ``uc_*`` temp profile dirs; skip *keep* if set."""
    tmp = tempfile.gettempdir()
    deleted = errors = 0
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
            "_cleanup_browser_profiles: deleted=%d skipped_locked=%d", deleted, errors
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
_JS_ERROR_TITLE = (
    "(() => {"
    "  const t = (document.title || '').toLowerCase();"
    "  return /access denied|forbidden|too many requests|blocked|error|unavailable/.test(t);"
    "})()"
)
# True when the document has finished loading and has real content (not a shell).
_JS_PAGE_READY = (
    "(() => {"
    "  if (document.readyState !== 'complete') return false;"
    "  const b = document.body;"
    "  if (!b) return false;"
    "  if (b.children.length === 1 && b.children[0].tagName === 'SCRIPT') return false;"
    "  const text = (b.innerText || '').trim().length;"
    "  const nodes = b.querySelectorAll('*').length;"
    "  return text >= 400 || nodes >= 40;"
    "})()"
)

_STATIC_ASSET_RESOURCE_TYPES: tuple[str, ...] = ("Image", "Font", "Stylesheet", "Media")
# Kept in sync with utils/antibot.py short-page heuristic.
_CONTENT_SHORT_THRESHOLD = 2500
# After the page looks ready, don't burn the full user settle — just a short cushion.
_READY_SETTLE_CAP_S = 1.5
_xvfb_proc: Any = None


def _random_fingerprint_args() -> list[str]:
    """Chrome launch args that vary per browser session."""
    size = random.choice(_FP_WINDOW_SIZES)
    lang = random.choice(_FP_LANGUAGES)
    logger.debug("Browser fingerprint — size=%s  lang=%s", size, lang)
    return [f"--window-size={size}", f"--lang={lang}"]


def _make_loop() -> asyncio.AbstractEventLoop:
    if sys.platform == "win32":
        return asyncio.ProactorEventLoop()
    return asyncio.new_event_loop()


def _stop_loop(
    loop: asyncio.AbstractEventLoop | None,
    thread: threading.Thread | None,
    timeout: float = 5.0,
) -> None:
    """Stop *loop*, join *thread*, then close the loop."""
    if loop is None:
        return
    try:
        loop.call_soon_threadsafe(loop.stop)
    except RuntimeError:
        pass
    if thread is not None:
        thread.join(timeout=timeout)
    if sys.platform == "win32":
        time.sleep(0.15)
    if not loop.is_closed():
        with contextlib.suppress(Exception):
            loop.close()


def _splash_url() -> str:
    """file:// URL for docs/static/logo.png, or about:blank if the file is missing."""
    logo = Path(__file__).resolve().parents[2] / "docs" / "static" / "logo.png"
    if logo.is_file():
        return logo.as_uri()
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
    """Fail Image/Font/Stylesheet/Media requests via CDP Fetch for *page*."""
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
        with contextlib.suppress(Exception):
            await page.send(_cdp_fetch.disable())


def _proxy_bypass_args(bypass_list: Any) -> list[str]:
    """Build ``--proxy-bypass-list=...`` from a domain/pattern list (or ``[]``)."""
    if not bypass_list:
        return []
    entries = [str(e).strip() for e in bypass_list if e and str(e).strip()]
    return [f"--proxy-bypass-list={';'.join(entries)}"] if entries else []


def _silence_browser() -> None:
    import logging

    import nodriver.core.util as _nd_util

    logging.getLogger("nodriver").setLevel(logging.WARNING)
    logging.getLogger("nodriver.core.util").setLevel(logging.CRITICAL)
    _nd_util.print = lambda *a, **kw: None


def _is_browser_crash(exc: BaseException) -> bool:
    return isinstance(exc, ConnectionRefusedError)


def _ensure_xvfb(headless: bool = False) -> None:
    """Start Xvfb when non-headless and no DISPLAY (no-op on Windows/headless)."""
    global _xvfb_proc
    if headless or sys.platform == "win32" or os.environ.get("DISPLAY"):
        return
    if _xvfb_proc is not None:
        return
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
    """Poll Navigation Timing status; error titles → 403; timeout → 200."""

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
    """Wait until the page looks loaded, then apply a short settle (not a long hang)."""
    await asyncio.sleep(0.15)

    if await page.evaluate(_JS_ERROR_TITLE):
        logger.debug("_smart_wait: blocked page title — skipping wait")
        return

    async def _is_ready() -> bool:
        return bool(await page.evaluate(_JS_PAGE_READY))

    def _settle_after_ready() -> float:
        # Page already usable — only a brief cushion for late hydration.
        if settle <= 0:
            return 0.0
        return min(settle, _READY_SETTLE_CAP_S)

    if await _is_ready():
        delay = _settle_after_ready()
        if delay:
            await asyncio.sleep(delay)
        return

    body_len = int(await page.evaluate(_JS_BODY_LEN))
    logger.debug(
        "_smart_wait: waiting for load (body_len=%d settle=%.1fs)",
        body_len,
        settle,
    )

    last_len = body_len
    stalled = 0
    poll_timeout = min(timeout, max(6.0, settle + 2.0))

    async def _poll() -> None:
        nonlocal last_len, stalled
        while True:
            if await page.evaluate(_JS_ERROR_TITLE):
                return

            if await _is_ready():
                # Confirm once more so we don't race a half-painted frame.
                await asyncio.sleep(0.3)
                if await _is_ready():
                    return

            current = int(await page.evaluate(_JS_BODY_LEN))
            growth = abs(current - last_len)
            # Treat tiny/analytic growth as stable so we don't reset forever.
            if growth < max(40, int(last_len * 0.03)):
                stalled += 1
                # ~1s stable with real content, or ~2.5s if still empty.
                limit = 3 if current >= 400 else 7
                if stalled >= limit:
                    logger.debug(
                        "_smart_wait: body stable at %d chars — stopping poll",
                        current,
                    )
                    return
            else:
                stalled = 0
                last_len = current

            await asyncio.sleep(0.35)

    try:
        await asyncio.wait_for(_poll(), timeout=poll_timeout)
    except asyncio.TimeoutError:
        logger.debug("_smart_wait: poll timed out after %.1fs", poll_timeout)

    delay = _settle_after_ready() if await _is_ready() else max(settle, 0.0)
    if delay > 0:
        await asyncio.sleep(delay)


class ProxyRelay:
    """Local TCP relay; ``await_closed`` cancels live handle tasks before teardown."""

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
        with contextlib.suppress(Exception):
            await self._server.wait_closed()


def _close_writer(w: asyncio.StreamWriter) -> None:
    """Close *w*, swallowing OSError/RuntimeError during loop teardown."""
    try:
        w.close()
    except (OSError, RuntimeError):
        pass


def _is_loop_shutdown_error(exc: BaseException) -> bool:
    """True when the browser loop/executor is tearing down mid-relay."""
    if isinstance(exc, asyncio.CancelledError):
        return True
    if not isinstance(exc, RuntimeError):
        return False
    msg = str(exc).lower()
    return (
        "after shutdown" in msg
        or "event loop is closed" in msg
        or "no running event loop" in msg
    )


async def _open_tcp_connection(
    host: str, port: int
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """Open TCP to *host*:*port*; IP literals use ``sock_connect`` (no getaddrinfo)."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return await asyncio.open_connection(host, port)

    loop = asyncio.get_running_loop()
    if isinstance(ip, ipaddress.IPv6Address):
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        addr: tuple[Any, ...] = (host, port, 0, 0)
    else:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = (host, port)
    sock.setblocking(False)
    try:
        await loop.sock_connect(sock, addr)
    except BaseException:
        sock.close()
        raise
    return await asyncio.open_connection(sock=sock)


async def _start_proxy_relay(proxy_url: str) -> tuple[ProxyRelay, int]:
    """Start a local auth-injecting relay to an upstream HTTP proxy."""
    return await _start_browser_relay(proxy_url=proxy_url)


async def _start_browser_relay(
    proxy_url: str | None = None,
    dns_overrides: dict[str, str] | None = None,
) -> tuple[ProxyRelay, int]:
    """Local CONNECT relay: DNS pin dial, upstream proxy auth, or direct dial."""
    dns_map = {h.lower(): ip for h, ip in (dns_overrides or {}).items()}

    up_host: str | None = None
    up_port = 3128
    auth_header = b""
    if proxy_url:
        parsed = urlparse(proxy_url if "://" in proxy_url else f"http://{proxy_url}")
        up_host = parsed.hostname
        up_port = parsed.port or 3128
        if parsed.username:
            token = base64.b64encode(
                f"{parsed.username}:{parsed.password or ''}".encode()
            ).decode()
            auth_header = b"Proxy-Authorization: Basic " + token.encode() + b"\r\n"

    if not up_host and not dns_map:
        raise ValueError("browser relay requires proxy_url and/or dns_overrides")

    relay_holder: list[ProxyRelay] = []

    async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
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

    async def _forward_upstream(
        upstream_writer: asyncio.StreamWriter,
        request_line: bytes,
        rest_headers: bytes,
        body: bytes,
    ) -> None:
        upstream_writer.write(request_line + b"\r\n" + auth_header + rest_headers)
        upstream_writer.write((b"\r\n\r\n" + body) if body else b"\r\n\r\n")
        await upstream_writer.drain()

    async def handle(
        client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter
    ) -> None:
        current = asyncio.current_task()
        if current is not None and relay_holder:
            relay_holder[0]._track(current)

        upstream_writer: asyncio.StreamWriter | None = None
        try:
            header = b""
            while b"\r\n\r\n" not in header:
                chunk = await client_reader.read(65536)
                if not chunk:
                    return
                header += chunk

            head, _, body = header.partition(b"\r\n\r\n")
            request_line, _, rest_headers = head.partition(b"\r\n")
            parts = request_line.split(None, 2)
            method = parts[0].upper() if parts else b""
            target = parts[1].decode(errors="replace") if len(parts) > 1 else ""

            connect_host: str | None = None
            connect_port: int | None = None
            if method == b"CONNECT" and target:
                host_part, sep, port_part = target.rpartition(":")
                if sep and port_part.isdigit():
                    connect_host = host_part.strip("[]").lower().rstrip(".")
                    connect_port = int(port_part)

            pinned_ip = dns_map.get(connect_host) if connect_host is not None else None
            dial_host = pinned_ip or connect_host
            dial_port = connect_port
            use_upstream = bool(up_host) and pinned_ip is None
            # Non-CONNECT / unparseable target without dial info falls back to upstream.
            if not use_upstream and (not dial_host or not dial_port):
                if not up_host:
                    return
                use_upstream = True

            if use_upstream:
                # Guaranteed by use_upstream / early return above.
                assert up_host is not None
                upstream_reader, upstream_writer = await _open_tcp_connection(
                    up_host, up_port
                )
                await _forward_upstream(
                    upstream_writer, request_line, rest_headers, body
                )
            else:
                # Guaranteed: missing dial info forces use_upstream or return.
                assert dial_host is not None and dial_port is not None
                if pinned_ip:
                    logger.debug(
                        "Browser relay DNS pin: %s:%s -> %s",
                        connect_host,
                        dial_port,
                        pinned_ip,
                    )
                upstream_reader, upstream_writer = await _open_tcp_connection(
                    dial_host, dial_port
                )
                if method == b"CONNECT":
                    client_writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                    await client_writer.drain()
                    if body:
                        upstream_writer.write(body)
                        await upstream_writer.drain()
                else:
                    upstream_writer.write(header)
                    await upstream_writer.drain()

            await asyncio.gather(
                _pipe(upstream_reader, client_writer),
                _pipe(client_reader, upstream_writer),
                return_exceptions=True,
            )
        except (OSError, asyncio.CancelledError):
            pass
        except RuntimeError as exc:
            # Browser restart closes the loop/executor while Chrome still has
            # CONNECT attempts hitting this relay — not a crawl failure.
            if not _is_loop_shutdown_error(exc):
                raise
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
    """Consecutive ban counter for browser session recycling."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._streak = 0
        self._restart_due = False
        self._last_restart = 0.0

    def record(self, banned: bool) -> bool:
        """Return True once when a restart should be attempted."""
        from ..config import config

        with self._lock:
            if not banned:
                self._streak = 0
                self._restart_due = False
                return False

            self._streak += 1
            if self._streak >= config.get("BROWSER_RESTART_AFTER_BANS"):
                self._restart_due = True

            if not self._restart_due:
                return False
            cooldown = config.get("BROWSER_RESTART_COOLDOWN_S")
            if self._last_restart and time.monotonic() - self._last_restart < cooldown:
                return False

            return True

    def acknowledge_restart(self) -> None:
        """Call when a ban-triggered browser restart is initiated."""
        with self._lock:
            self._streak = 0
            self._restart_due = False
            self._last_restart = time.monotonic()
