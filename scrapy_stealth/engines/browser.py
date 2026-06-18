from __future__ import annotations

import asyncio
import contextlib
import sys
import threading
from typing import Any

from scrapy.http import Request, Response

from ..config import config
from ..detectors.antibot import AntiBotDetector
from ..exceptions import (
    StealthBrowserNotFoundError,
    StealthConnectionError,
    StealthTimeoutError,
)
from ..utils.browser import (
    _BROWSER_ARGS,
    _JS_HTML,
    _JS_IS_CHROME_ERROR,
    BanStreakTracker,
    _block_static_assets,
    _cdp_snapshot,
    _ensure_xvfb,
    _is_browser_crash,
    _make_loop,
    _proxy_bypass_args,
    _random_fingerprint_args,
    _silence_browser,
    _smart_wait,
    _splash_url,
    _start_proxy_relay,
    _stop_loop,
    _wait_for_status,
)
from ..utils.console import console
from ..utils.logger import get_logger
from ..utils.meta import _get_meta_data
from ..utils.patch import patch_nodriver
from ..utils.response import StealthResponse
from .base import BaseEngine

patch_nodriver()

logger = get_logger()


class BrowserEngine(BaseEngine):
    """
    Chrome engine via DevTools Protocol (no WebDriver overhead).

    - No proxy: one persistent browser; each request opens a new tab then closes it.
    - With proxy: one persistent browser started with ``--proxy-server`` pointing at a
      local auth-injecting relay; each request opens a new tab then closes it.
    """

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        super().__init__(profile, timeout)
        self._browser: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._tab_sem: asyncio.Semaphore | None = None
        # Restarts Chrome (fresh fingerprint/cookies/CDP session) after N
        # consecutive banned/challenged responses; resets on any clean response.
        self._bans = BanStreakTracker()

        # Proxy-relay state — created once on first proxied request.
        self._relay_server: Any = None
        self._relay_port: int | None = None
        self._relay_lock = threading.Lock()

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
            args.append("--disable-gpu")
            args.append("--disable-gpu-sandbox")
            args.append("--disable-software-rasterizer")
        no_sandbox = config.get("BROWSER_NO_SANDBOX")
        if no_sandbox is None:
            no_sandbox = hasattr(os, "getuid") and os.getuid() == 0
        if no_sandbox:
            args.append("--no-sandbox")
            args.append("--disable-setuid-sandbox")
            args.append("--disable-dev-shm-usage")
        if proxy_port is not None:
            args.append(f"--proxy-server=http://127.0.0.1:{proxy_port}")
            # Domains the user listed must reach the origin directly, never the
            # proxy relay. Only meaningful alongside --proxy-server.
            args.extend(_proxy_bypass_args(config.get("BROWSER_PROXY_BYPASS_LIST")))
        # Append fingerprint args last so they always win over any conflicting base arg.
        args.extend(fingerprint_args or _random_fingerprint_args())
        return args

    def _is_root(self) -> bool:
        import os

        return hasattr(os, "getuid") and os.getuid() == 0

    async def _start_browser(
        self,
        headless: bool,
        proxy_port: int | None = None,
        fingerprint_args: list[str] | None = None,
    ) -> Any:
        """Start a browser instance with proper error handling for executable path."""
        import nodriver as _nd

        _ensure_xvfb(headless)

        executable_path: str | None = config.get("BROWSER_EXECUTABLE_PATH")
        try:
            kwargs: dict[str, Any] = {
                "browser_args": self._build_args(
                    headless,
                    proxy_port=proxy_port,
                    fingerprint_args=fingerprint_args,
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
        except FileNotFoundError as exc:
            if executable_path:
                raise StealthBrowserNotFoundError(
                    f"Browser binary not found at the configured path: {executable_path!r}. "
                    "Check BROWSER_EXECUTABLE_PATH in your settings or config."
                ) from exc
            raise StealthBrowserNotFoundError(
                "Browser binary not found. Install Google Chrome or Chromium, or set "
                "BROWSER_EXECUTABLE_PATH to point to your browser binary (e.g. Brave)."
            ) from exc

    # Benign Windows Proactor teardown WinErrors raised when in-flight overlapped
    # socket ops (the proxy-relay accept loop, tab pipes) are aborted as the event
    # loop stops during a browser restart/shutdown — not real failures.
    #   10054 = WSAECONNRESET           (connection reset by peer)
    #     995 = ERROR_OPERATION_ABORTED (I/O cancelled by thread exit / app request)
    #      64 = ERROR_NETNAME_DELETED   (network name no longer available)
    _BENIGN_WINERRORS: frozenset[int] = frozenset({10054, 995, 64})

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
            and getattr(exc, "winerror", None)
            in BrowserEngine._BENIGN_WINERRORS
        ):
            return
        loop.default_exception_handler(context)

    def _run_loop(self) -> None:
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        self._loop.set_exception_handler(self._loop_exception_handler)
        self._loop.run_forever()

    def _ensure_browser(self, headless: bool, proxy: str | None = None) -> None:
        """
        Ensure the persistent browser is running.  When a proxy is provided the
        browser is started with ``--proxy-server`` pointing at the local relay;
        without a proxy the browser connects directly.
        """
        with self._lock:
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

    async def _start(self, headless: bool, proxy: str | None = None) -> Any:
        _ensure_xvfb(headless)
        _silence_browser()

        proxy_port: int | None = None
        if proxy:
            server, proxy_port = await _start_proxy_relay(proxy)
            self._relay_server = server
            self._relay_port = proxy_port
            logger.debug("Proxy relay started on 127.0.0.1:%d", proxy_port)

        # Draw a fresh fingerprint for this browser lifetime.  _start_browser
        # passes it to _build_args so the same values end up in the process
        # args — no second random draw happens inside _build_args.
        browser = await self._start_browser(headless, proxy_port=proxy_port)

        # Warm up the renderer on the default tab Chrome opens at startup.
        try:
            await browser.main_tab.get(_splash_url())
            await browser.main_tab.wait()
        except Exception:
            pass

        self._tab_sem = asyncio.Semaphore(config.get("BROWSER_MAX_TABS"))
        return browser

    def close(self) -> None:
        if self._loop is None:
            return
        try:
            asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop).result(
                timeout=10
            )
        except Exception:
            pass
        _stop_loop(self._loop, self._thread)

    async def _shutdown(self) -> None:
        if self._relay_server is not None:
            self._relay_server.close()
            self._relay_server = None
            self._relay_port = None
        if self._browser is not None:
            self._browser.stop()
            self._browser = None

    def _reset_browser(
        self,
        headless: bool,
        dead_browser: Any = None,
        proxy: str | None = None,
    ) -> None:
        with self._lock:
            if dead_browser is not None and self._browser is not dead_browser:
                return
            if self._browser is not None:
                try:
                    self._browser.stop()
                except Exception:
                    pass
                self._browser = None
            self._tab_sem = None

            # Tear down the old relay so a fresh one is created with the new loop.
            if self._relay_server is not None:
                try:
                    self._relay_server.close()
                except Exception:
                    pass
                self._relay_server = None
                self._relay_port = None

            # Join the old loop/thread before starting a new one — otherwise it
            # keeps polling its selector after the new loop exists and can crash
            # on in-flight I/O (see _stop_loop docstring).
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

    async def _do_fetch(
        self,
        url: str,
        settle: float,
        snapshot: bool = False,
        block_assets: bool = False,
    ) -> tuple[bytes, int, bytes | None]:
        """
        Open a new browser context (isolated tab), fetch *url*, then close
        the context.  The caller is responsible for holding ``_tab_sem`` before
        calling this coroutine so concurrency is capped at ``BROWSER_MAX_TABS``.

        Proxy credentials are already baked into the browser via the relay
        started in ``_start()``, so no special handling is needed here.
        """
        html: Any = ""
        status: Any = 200
        shot: bytes | None = None

        assert self._tab_sem is not None

        async with self._tab_sem:
            page = await self._browser.get(url, new_tab=True)
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
                try:
                    await page.close()
                except Exception:
                    pass

        return str(html).encode(errors="replace"), int(status), shot

    def _maybe_restart(
        self, headless: bool, proxy: str | None, response: Response | None
    ) -> None:
        """Restart Chrome once BanStreakTracker reports N consecutive bans."""
        banned = response is not None and (
            AntiBotDetector.is_blocked(response)
            or AntiBotDetector.is_js_challenge(response)
        )
        if self._bans.record(banned):
            console.info(
                f"Restarting browser after "
                f"{config.get('BROWSER_RESTART_AFTER_BANS')} consecutive bans"
            )
            self._reset_browser(headless, self._browser, proxy=proxy)

    def _execute(self, request: Request) -> Response | None:
        ctx = self._ctx(request)
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

            # Ensure the single persistent browser is up (proxy-aware).
            self._ensure_browser(headless=headless, proxy=ctx.proxy or None)

            body: bytes = b""
            status: int = 200
            shot: bytes | None = None

            for attempt in range(2):
                try:
                    assert self._loop is not None
                    future = asyncio.run_coroutine_threadsafe(
                        self._do_fetch(request.url, settle, snap, block_assets),
                        self._loop,
                    )
                    body, status, shot = future.result(timeout=ctx.timeout)
                    break
                except (ConnectionRefusedError, RuntimeError) as exc:
                    if attempt == 0 and _is_browser_crash(exc):
                        console.warning(f"Browser crashed, restarting: {exc}")
                        self._reset_browser(
                            headless, self._browser, proxy=ctx.proxy or None
                        )
                    else:
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

            # Restart Chrome after BROWSER_RESTART_AFTER_BANS consecutive bans.
            self._maybe_restart(headless, ctx.proxy or None, response)

            return response

        except TimeoutError as exc:
            raise StealthTimeoutError(
                f"Browser engine timed out after {ctx.timeout}s fetching {request.url!r}"
            ) from exc
        except StealthBrowserNotFoundError:
            raise
        except StealthConnectionError:
            raise
        except (ConnectionRefusedError, OSError) as exc:
            raise StealthConnectionError(
                f"Browser engine connection failed fetching {request.url!r}"
            ) from exc
        except Exception as exc:
            try:
                from websockets.exceptions import ConnectionClosedError as _WsClosed

                if isinstance(exc, _WsClosed):
                    raise StealthConnectionError(
                        f"Browser tab closed unexpectedly fetching {request.url!r}"
                    ) from exc
            except ImportError:
                pass
            try:
                from nodriver.core.connection import ProtocolException as _ProtoExc

                if isinstance(exc, _ProtoExc):
                    raise StealthConnectionError(
                        f"Browser target lost fetching {request.url!r}"
                    ) from exc
            except ImportError:
                pass
            logger.exception("Browser engine request failed: %s", exc)
            return None
