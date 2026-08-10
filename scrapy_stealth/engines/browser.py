from __future__ import annotations

import asyncio
import contextlib
import logging
import sys
import threading
import weakref
from concurrent import futures
from typing import Any

from scrapy.http import Request, Response

from ..config import config
from ..detectors.antibot import AntiBotDetector
from ..exceptions import (
    StealthBrowserNotFoundError,
    StealthConnectionError,
    StealthTimeoutError,
    raise_stealth,
)
from ..utils.browser import (
    _BROWSER_ARGS,
    _JS_HTML,
    _JS_IS_CHROME_ERROR,
    ProxyRelay,
    _block_static_assets,
    _cdp_snapshot,
    _cleanup_browser_temp_data,
    _ensure_xvfb,
    _is_browser_crash,
    _make_loop,
    _proxy_bypass_args,
    _random_fingerprint_args,
    _silence_browser,
    _smart_wait,
    _splash_url,
    _start_browser_relay,
    _stop_loop,
    _wait_for_status,
)
from ..utils.browser.patch import patch_nodriver
from ..utils.browser.session import BanStreakTracker
from ..utils.core.console import console
from ..utils.core.logger import get_logger
from ..utils.core.meta import _get_meta_data
from ..utils.core.response import StealthResponse
from ..utils.network.dns import (
    dns_fingerprint,
    resolve_dns_overrides,
    validate_dns_overrides,
)
from .base import BaseEngine

patch_nodriver()

logger = get_logger()


class _AsyncioTeardownFilter(logging.Filter):
    """Suppress benign asyncio teardown noise during browser restart."""

    _TRANSIENT_TASK_MARKERS = (
        "StealthConnectionError",
        "Connection closed",
        "ConnectionError",
        "InvalidMessage",
        "_run_fetch",
        "update_targets",
        "sleep()",
    )

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "Event loop is closed" in msg and (
            "callback" in msg
            or "Exception in callback" in msg
            or "calling callback" in msg
        ):
            return False
        if "Task was destroyed but it is pending" in msg:
            return False
        if "Task exception was never retrieved" in msg and any(
            marker in msg for marker in self._TRANSIENT_TASK_MARKERS
        ):
            return False
        return True


logging.getLogger("concurrent.futures").addFilter(_AsyncioTeardownFilter())
logging.getLogger("asyncio").addFilter(_AsyncioTeardownFilter())

if sys.platform == "win32":
    _orig_unraisablehook = sys.unraisablehook

    def _win_unraisablehook(unraisable: sys.UnraisableHookArgs) -> None:
        exc = unraisable.exc_value
        if isinstance(exc, ValueError) and "closed pipe" in str(exc):
            return
        _orig_unraisablehook(unraisable)

    sys.unraisablehook = _win_unraisablehook


def _browser_fetch_timeout(request_timeout: int | float, settle: float) -> float:
    # Cover status poll (~8s), settle/smart-wait, and tab-queue headroom.
    return request_timeout + settle + 12.0


class BrowserEngine(BaseEngine):
    """Chrome via CDP: one persistent browser; each request opens then closes a tab."""

    # Benign Windows Proactor teardown WinErrors (10054/995/64).
    _BENIGN_WINERRORS: frozenset[int] = frozenset({10054, 995, 64})

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        super().__init__(profile, timeout)
        self._browser: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._restart_cv = threading.Condition(self._lock)
        self._restarting = False
        self._tab_sem: asyncio.Semaphore | None = None
        # Restarts Chrome (fresh fingerprint/cookies/CDP session) after N
        # consecutive banned/challenged responses; resets on any clean response.
        self._bans = BanStreakTracker()

        # Proxy-relay state — created once on first proxied request.
        self._relay_server: ProxyRelay | None = None
        self._relay_port: int | None = None
        self._relay_lock = threading.Lock()
        # In-flight _run_fetch tasks — cancelled before loop teardown so concurrent
        # Scrapy threads are not left with orphaned coroutines on browser restart.
        self._fetch_tasks: weakref.WeakSet[asyncio.Task[Any]] = weakref.WeakSet()
        # DNS overrides applied on the *next* Chrome launch (config + per-request).
        self._dns_overrides: dict[str, str] = {}
        self._launched_dns: tuple[tuple[str, str], ...] = ()

    @property
    def driver_name(self) -> str:
        return "browser"

    def _build_args(
        self,
        headless: bool,
        proxy_port: int | None = None,
        fingerprint_args: list[str] | None = None,
    ) -> list[str]:
        import os

        # _BROWSER_ARGS has no --window-size; _random_fingerprint_args() supplies it.
        args = list(_BROWSER_ARGS)
        if headless:
            args.append("--headless=new")
        if sys.platform != "win32":
            args.extend(
                (
                    "--disable-gpu",
                    "--disable-gpu-sandbox",
                    "--disable-software-rasterizer",
                )
            )
        no_sandbox = config.get("BROWSER_NO_SANDBOX")
        if no_sandbox is None:
            no_sandbox = hasattr(os, "getuid") and os.getuid() == 0
        if no_sandbox:
            args.extend(
                ("--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage")
            )
        if proxy_port is not None:
            args.append(f"--proxy-server=http://127.0.0.1:{proxy_port}")
            # DNS-pinned hosts must stay on the relay — do not add them to bypass.
            args.extend(_proxy_bypass_args(config.get("BROWSER_PROXY_BYPASS_LIST")))
        # Append fingerprint args last so they always win over any conflicting base arg.
        args.extend(fingerprint_args or _random_fingerprint_args())
        return args

    def _effective_dns_overrides(self) -> dict[str, str]:
        """DNS map for the next/current browser relay (request meta wins via preset)."""
        src = self._dns_overrides or (config.get("STEALTH_DNS_OVERRIDES") or {})
        return validate_dns_overrides(src)

    def _is_root(self) -> bool:
        import os

        return hasattr(os, "getuid") and os.getuid() == 0

    async def _start_browser(
        self,
        headless: bool,
        proxy_port: int | None = None,
        fingerprint_args: list[str] | None = None,
    ) -> Any:
        """Start nodriver; map missing binary to StealthBrowserNotFoundError."""
        import nodriver as _nd

        _ensure_xvfb(headless)

        executable_path: str | None = config.get("BROWSER_EXECUTABLE_PATH")
        try:
            kwargs: dict[str, Any] = {
                "browser_args": self._build_args(
                    headless, proxy_port=proxy_port, fingerprint_args=fingerprint_args
                ),
                "headless": headless,
                "sandbox": not self._is_root(),
            }
            if executable_path:
                kwargs["browser_executable_path"] = executable_path
                logger.debug(
                    "Initializing browser with executable path: %s", executable_path
                )
            return await _nd.start(**kwargs)
        except FileNotFoundError:
            if executable_path:
                raise_stealth(
                    StealthBrowserNotFoundError,
                    f"Browser binary not found at the configured path: {executable_path!r}. "
                    "Check BROWSER_EXECUTABLE_PATH in your settings or config.",
                )
            raise_stealth(
                StealthBrowserNotFoundError,
                "Browser binary not found. Install Google Chrome or Chromium, or set "
                "BROWSER_EXECUTABLE_PATH to point to your browser binary (e.g. Brave).",
            )

    @staticmethod
    def _loop_exception_handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
        exc = context.get("exception")
        # Suppress Windows Proactor pipe-teardown noise on tab/browser close.
        if isinstance(
            exc, (ConnectionRefusedError, ConnectionResetError, BrokenPipeError)
        ):
            return
        if (
            isinstance(exc, OSError)
            and getattr(exc, "winerror", None) in BrowserEngine._BENIGN_WINERRORS
        ):
            return
        # InvalidStateError is raised inside the Proactor's _poll when a
        # WinError-995 I/O-abort callback fires against an already-done future
        # during loop teardown.  It never reaches the loop's exception handler
        # through the normal path (it propagates through _run_loop instead), but
        # suppress it here as well for any edge case where it does arrive.
        if isinstance(exc, asyncio.InvalidStateError):
            return
        # Orphaned nodriver / fetch tasks during browser restart.
        if isinstance(exc, (ConnectionError, StealthConnectionError)):
            return
        loop.default_exception_handler(context)

    def _run_loop(self) -> None:
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        self._loop.set_exception_handler(self._loop_exception_handler)
        try:
            self._loop.run_forever()
        except asyncio.InvalidStateError:
            # Last-resort catch: WinError-995 abort during Proactor teardown can
            # surface as InvalidStateError bubbling out of run_forever() on
            # Python 3.13+ when a future's set_exception() races with loop.stop().
            # The loop is already stopping at this point; swallowing the exception
            # is safe — the restart/close path in _stop_loop handles cleanup.
            pass

    def _wait_for_browser_ready(self) -> None:
        with self._lock:
            while self._restarting:
                self._restart_cv.wait()

    def _ensure_browser(self, headless: bool, proxy: str | None = None) -> None:
        """Ensure the persistent browser is running (proxy/DNS-relay aware)."""
        with self._lock:
            while self._restarting:
                self._restart_cv.wait()
            self._ensure_browser_unlocked(headless, proxy=proxy)

    def _ensure_browser_for_dns(self, headless: bool, proxy: str | None = None) -> None:
        """Restart Chrome when the effective DNS map differs from the relay's map."""
        wanted = dns_fingerprint(self._effective_dns_overrides())
        with self._lock:
            while self._restarting:
                self._restart_cv.wait()
            needs_restart = self._browser is not None and wanted != self._launched_dns
            browser = self._browser
        if needs_restart:
            logger.debug(
                "Restarting browser to apply DNS override(s): %s", dict(wanted)
            )
            self._reset_browser(headless, browser, proxy=proxy)

    def _ensure_browser_unlocked(
        self, headless: bool, proxy: str | None = None
    ) -> None:
        if self._browser is not None:
            return
        loop = _make_loop()
        self._loop = loop
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        future = asyncio.run_coroutine_threadsafe(
            self._start(headless, proxy=proxy), loop
        )
        self._browser = future.result(timeout=30)
        self._launched_dns = dns_fingerprint(self._effective_dns_overrides())
        if self._launched_dns:
            logger.debug(
                "Browser launched with DNS override(s) via local relay: %s",
                dict(self._launched_dns),
            )

    async def _start(self, headless: bool, proxy: str | None = None) -> Any:
        _ensure_xvfb(headless)
        _silence_browser()

        dns_overrides = self._effective_dns_overrides()
        proxy_port: int | None = None
        # Local CONNECT relay is required for DNS pins (Chrome host-resolver-rules
        # is unreliable) and for upstream proxy auth injection.
        if proxy or dns_overrides:
            server, proxy_port = await _start_browser_relay(
                proxy_url=proxy,
                dns_overrides=dns_overrides or None,
            )
            self._relay_server = server
            self._relay_port = proxy_port
            logger.debug(
                "Browser relay started on 127.0.0.1:%d (proxy=%s dns=%s)",
                proxy_port,
                bool(proxy),
                dict(dns_overrides) if dns_overrides else {},
            )

        # Draw a fresh fingerprint for this browser lifetime.  _start_browser
        # passes it to _build_args so the same values end up in the process
        # args — no second random draw happens inside _build_args.
        browser = await self._start_browser(headless, proxy_port=proxy_port)
        with contextlib.suppress(Exception):
            await browser.main_tab.get(_splash_url())
            await browser.main_tab.wait()

        self._tab_sem = asyncio.Semaphore(config.get("BROWSER_MAX_TABS"))
        return browser

    def close(self) -> None:
        if self._loop is None:
            return
        loop, thread = self._loop, self._thread
        self._loop = self._thread = None
        with contextlib.suppress(Exception):
            asyncio.run_coroutine_threadsafe(self._shutdown(), loop).result(timeout=3)
        _stop_loop(loop, thread, timeout=2.0)

    def _track_fetch_task(self, task: asyncio.Task[Any]) -> None:
        self._fetch_tasks.add(task)

    async def _drain_loop_tasks(self) -> None:
        current = asyncio.current_task()
        pending = [t for t in asyncio.all_tasks() if t is not current and not t.done()]
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
            await asyncio.sleep(0)

    @staticmethod
    def _is_restart_transient(exc: BaseException) -> bool:
        if isinstance(
            exc,
            (
                StealthConnectionError,
                ConnectionError,
                ConnectionRefusedError,
                ConnectionResetError,
                BrokenPipeError,
            ),
        ):
            return True
        if _is_browser_crash(exc):
            return True
        return "websockets" in getattr(type(exc), "__module__", "")

    async def _shutdown(self) -> None:
        if self._browser is not None:
            with contextlib.suppress(Exception):
                self._browser.stop()
            self._browser = None
            _cleanup_browser_temp_data()
        await self._drain_loop_tasks()
        if self._relay_server is not None:
            with contextlib.suppress(Exception):
                await self._relay_server.await_closed()
            self._relay_server = None
            self._relay_port = None

    def _reset_browser(
        self,
        headless: bool,
        dead_browser: Any = None,
        proxy: str | None = None,
    ) -> None:
        with self._lock:
            self._restarting = True
            try:
                if dead_browser is not None and self._browser is not dead_browser:
                    return
                if self._browser is not None:
                    with contextlib.suppress(Exception):
                        self._browser.stop()
                    self._browser = None
                    _cleanup_browser_temp_data()
                self._tab_sem = None
                self._launched_dns = ()

                if self._loop is not None:
                    with contextlib.suppress(Exception):
                        asyncio.run_coroutine_threadsafe(
                            self._drain_loop_tasks(), self._loop
                        ).result(timeout=3)

                if self._relay_server is not None and self._loop is not None:
                    with contextlib.suppress(Exception):
                        asyncio.run_coroutine_threadsafe(
                            self._relay_server.await_closed(), self._loop
                        ).result(timeout=2)
                    self._relay_server = None
                    self._relay_port = None

                _stop_loop(self._loop, self._thread)

                loop = _make_loop()
                self._loop = loop
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()
                future = asyncio.run_coroutine_threadsafe(
                    self._start(headless, proxy=proxy), loop
                )
                self._browser = future.result(timeout=30)
                console.success("Browser restarted successfully")
            finally:
                self._restarting = False
                self._restart_cv.notify_all()

    async def _do_fetch(
        self,
        url: str,
        settle: float,
        snapshot: bool = False,
        block_assets: bool = False,
    ) -> tuple[bytes, int, bytes | None]:
        """Open a CDP target, fetch *url*, then close the tab."""
        import nodriver.cdp.target as _cdp_target

        html: Any = ""
        status: Any = 200
        shot: bytes | None = None

        if self._browser is None:
            raise StealthConnectionError("Browser is not running")

        browser = self._browser
        assert self._tab_sem is not None

        async with self._tab_sem:
            # Create the target and navigate it atomically via CDP.
            # create_target returns the new target_id immediately — no
            # update_targets() race, no wrong-tab ambiguity.
            target_id = await browser.send(
                # enable_begin_frame_control=True freezes painting until BeginFrame
                # is issued (black/blank tab) — leave it off for normal loads.
                _cdp_target.create_target(url, enable_begin_frame_control=False)
            )
            await browser.update_targets()
            page = next(
                (t for t in browser.targets if t.target.target_id == target_id),
                None,
            )
            if page is None:
                raise StealthConnectionError(
                    f"Browser engine could not find new tab for {url!r}"
                )
            await page.attach()

            try:
                async with contextlib.AsyncExitStack() as stack:
                    if block_assets:
                        await stack.enter_async_context(_block_static_assets(page))

                    await page.wait()

                    if await page.evaluate(_JS_IS_CHROME_ERROR):
                        raise StealthConnectionError(
                            f"Browser engine connection failed fetching {url!r}"
                        )

                    # Poll until Navigation Timing exposes a real (non-zero) status.
                    status = await _wait_for_status(page)

                    # Skip content wait on error responses — return immediately.
                    if 200 <= status < 300:
                        await _smart_wait(page, settle)

                    html = await page.evaluate(_JS_HTML)
                    if snapshot:
                        shot = await _cdp_snapshot(page)
            finally:
                with contextlib.suppress(Exception):
                    await page.close()
                with contextlib.suppress(Exception):
                    await page.aclose()

        return str(html).encode(errors="replace"), int(status), shot

    def _maybe_restart(
        self, headless: bool, proxy: str | None, response: Response | None
    ) -> None:
        """Restart Chrome once BanStreakTracker reports N consecutive bans."""
        banned = response is not None and AntiBotDetector.is_browser_session_ban(
            response
        )
        with self._lock:
            if self._restarting:
                # Restart logic ignores in-flight results, but stats still count
                # every completed browser response.
                self._record_response(response, banned)
                return

        should_recycle = self._bans.record(banned)
        self._record_response(response, banned)
        if not should_recycle:
            return

        with self._lock:
            if self._restarting:
                return

        console.info(
            f"Restarting browser after "
            f"{config.get('STEALTH_RECYCLE_AFTER_BANS')} consecutive bans"
        )
        self._bans.acknowledge_restart()
        # Fresh Chrome fingerprint comes from _random_fingerprint_args on restart;
        # keep / rotate proxy for subsequent requests without explicit meta.
        if proxy and not (config.get("STEALTH_PROXIES") or []):
            self._default_proxy = proxy
        new_proxy = self._rotate_default_proxy()
        self._reset_browser(headless, self._browser, proxy=proxy or new_proxy)
        self._record_recycle(self._default_profile, proxy or new_proxy)

    def _execute(self, request: Request) -> Response | None:
        ctx = self._ctx(request)
        self._record_request_identity(ctx.profile, ctx.proxy)
        try:
            headless: bool = _get_meta_data(
                request, "headless", config.get("BROWSER_HEADLESS")
            )
            settle: float = _get_meta_data(
                request, "settle", config.get("BROWSER_SETTLE_S")
            )
            snap: bool = _get_meta_data(request, "snapshot", False)
            # Snapshot needs the real rendered page, so it's never blocked —
            # even if static_assets_block is on globally or per-request.
            block_assets: bool = not snap and _get_meta_data(
                request,
                "static_assets_block",
                config.get("BROWSER_STATIC_ASSETS_BLOCK"),
            )

            logger.debug(
                "Initializing browser engine (headless=%s & settle=%ss)",
                headless,
                settle,
            )

            # Ensure the single persistent browser is up (proxy / DNS-relay aware).
            # DNS pins use a local CONNECT relay (not Chrome host-resolver-rules).
            body: bytes = b""
            status: int = 200
            shot: bytes | None = None
            self._dns_overrides = dict(resolve_dns_overrides(request))
            self._record_dns(len(self._dns_overrides))

            for attempt in range(5):
                task: asyncio.Task[Any] | None = None
                loop: asyncio.AbstractEventLoop | None = None

                async def _run_fetch() -> tuple[bytes, int, bytes | None]:
                    nonlocal task
                    current = asyncio.current_task()
                    assert current is not None
                    task = current
                    self._track_fetch_task(task)
                    try:
                        return await self._do_fetch(
                            request.url, settle, snap, block_assets
                        )
                    finally:
                        self._fetch_tasks.discard(task)

                self._wait_for_browser_ready()
                self._ensure_browser_for_dns(headless, ctx.proxy or None)
                with self._lock:
                    self._ensure_browser_unlocked(
                        headless=headless, proxy=ctx.proxy or None
                    )
                    loop = self._loop
                    assert loop is not None
                    future = asyncio.run_coroutine_threadsafe(_run_fetch(), loop)

                try:
                    body, status, shot = future.result(
                        timeout=_browser_fetch_timeout(ctx.timeout, settle)
                    )
                    break
                except TimeoutError:
                    # Cancel via the snapshotted loop — if it's already
                    # closed, swallow silently (the task is dead anyway).
                    if task is not None and loop is not None and not loop.is_closed():
                        with contextlib.suppress(RuntimeError):
                            loop.call_soon_threadsafe(task.cancel)
                    raise
                except (
                    futures.CancelledError,
                    asyncio.CancelledError,
                    StealthConnectionError,
                ):
                    self._wait_for_browser_ready()
                    if attempt < 4:
                        continue
                    raise
                except Exception as exc:
                    if attempt < 4 and self._is_restart_transient(exc):
                        self._wait_for_browser_ready()
                        continue
                    if attempt < 4 and _is_browser_crash(exc):
                        console.warning(f"Browser crashed, restarting: {exc}")
                        self._reset_browser(
                            headless, self._browser, proxy=ctx.proxy or None
                        )
                        continue
                    raise

            logger.debug(
                "Browser engine fetched %s  status=%s  size=%d bytes",
                request.url,
                status,
                len(body),
            )
            response = StealthResponse(
                request=request,
                status=status,
                headers={"content-type": "text/html; charset=utf-8"},
                body=body,
                _meta={"snapshot_content": shot} if shot is not None else None,
                _flags=["browser"],
            )

            # Restart Chrome after STEALTH_RECYCLE_AFTER_BANS consecutive bans.
            self._maybe_restart(headless, ctx.proxy or None, response)

            return response

        except TimeoutError:
            raise_stealth(
                StealthTimeoutError,
                f"Browser engine timed out after {ctx.timeout}s fetching {request.url!r}",
            )
        except (
            StealthBrowserNotFoundError,
            StealthConnectionError,
            StealthTimeoutError,
        ):
            raise
        except (ConnectionRefusedError, OSError):
            raise_stealth(
                StealthConnectionError,
                f"Browser engine connection failed fetching {request.url!r}",
            )
        except Exception as exc:
            for mod, attr, msg in (
                (
                    "websockets.exceptions",
                    "ConnectionClosedError",
                    f"Browser tab closed unexpectedly fetching {request.url!r}",
                ),
                (
                    "nodriver.core.connection",
                    "ProtocolException",
                    f"Browser target lost fetching {request.url!r}",
                ),
            ):
                try:
                    cls = getattr(__import__(mod, fromlist=[attr]), attr)
                except ImportError:
                    continue
                if isinstance(exc, cls):
                    raise_stealth(StealthConnectionError, msg)
            if isinstance(exc, (futures.CancelledError, asyncio.CancelledError)):
                logger.debug(
                    "Browser fetch cancelled during restart for %s", request.url
                )
                return None
            logger.error("Browser engine request failed: %r", exc)
            return None
