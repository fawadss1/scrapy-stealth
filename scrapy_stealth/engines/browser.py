from __future__ import annotations

import asyncio
import sys
import threading
from typing import Any

from scrapy.http import Request, Response

from ..config import config
from ..exceptions import (
    StealthBrowserNotFoundError,
    StealthConnectionError,
    StealthTimeoutError,
)
from ..utils.browser import (
    _BROWSER_ARGS,
    _JS_HTML,
    _JS_IS_CHROME_ERROR,
    _JS_STATUS,
    _cdp_snapshot,
    _ensure_xvfb,
    _is_browser_crash,
    _make_loop,
    _silence_browser,
    _splash_url,
    _start_proxy_relay,
    _wait_for_content,
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
    - With proxy: fresh browser per request so every request gets a new exit IP.
    """

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        super().__init__(profile, timeout)
        self._browser: Any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._tab_sem: asyncio.Semaphore | None = None
        self._request_count: int = 0
        self._count_lock = threading.Lock()

    def _build_args(self, headless: bool) -> list[str]:
        import os

        args = list(_BROWSER_ARGS)
        if headless:
            args.append("--headless=new")
        # On Linux the non-headless display is Xvfb, which has no GPU, so disable
        # GPU acceleration or Chrome will hang/crash during GPU init on startup.
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
        return args

    def _is_root(self) -> bool:
        import os

        return hasattr(os, "getuid") and os.getuid() == 0

    async def _start_browser(
        self, headless: bool, extra_args: list[str] | None = None
    ) -> Any:
        """Start a browser instance with proper error handling for executable path."""
        import nodriver as _nd

        # When running non-headless, enforce a display: on Linux this starts Xvfb
        # if needed and raises if Xvfb is unavailable, rather than silently
        # falling back to detectable headless mode. No-op when headless=True.
        _ensure_xvfb(headless)

        executable_path: str | None = config.get("BROWSER_EXECUTABLE_PATH")
        try:
            kwargs: dict[str, Any] = {
                "browser_args": self._build_args(headless) + (extra_args or []),
                "headless": headless,
                # nodriver's start() takes `sandbox` (not `no_sandbox`); False adds
                # --no-sandbox, required when running as root in a container.
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

    @staticmethod
    def _loop_exception_handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
        if isinstance(context.get("exception"), ConnectionRefusedError):
            return  # suppress nodriver background CDP polling noise on restart
        loop.default_exception_handler(context)

    def _run_loop(self) -> None:
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        self._loop.set_exception_handler(self._loop_exception_handler)
        self._loop.run_forever()

    def _ensure_browser(self, headless: bool) -> None:
        with self._lock:
            if self._browser is not None:
                return
            loop = _make_loop()
            self._loop = loop
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            future = asyncio.run_coroutine_threadsafe(self._start(headless), loop)
            self._browser = future.result(timeout=30)

    async def _start(self, headless: bool) -> Any:

        _ensure_xvfb(headless)
        _silence_browser()
        browser = await self._start_browser(headless)
        self._tab_sem = asyncio.Semaphore(config.get("BROWSER_MAX_TABS"))
        return browser

    def close(self) -> None:
        if self._loop is None:
            return
        loop = self._loop
        try:
            asyncio.run_coroutine_threadsafe(self._shutdown(), loop).result(timeout=10)
        except Exception:
            pass
        finally:
            loop.call_soon_threadsafe(loop.stop)

    async def _shutdown(self) -> None:
        if self._browser is not None:
            self._browser.stop()
            self._browser = None

    def _reset_browser(self, headless: bool, dead_browser: Any = None) -> None:
        with self._lock:
            if dead_browser is not None and self._browser is not dead_browser:
                return  # another thread already restarted
            if self._browser is not None:
                try:
                    self._browser.stop()
                except Exception:
                    pass
                self._browser = None
            self._tab_sem = None
            if self._loop is not None:
                try:
                    self._loop.call_soon_threadsafe(self._loop.stop)
                except Exception:
                    pass
                self._loop = None
            self._thread = None
            loop = _make_loop()
            self._loop = loop
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            future = asyncio.run_coroutine_threadsafe(self._start(headless), loop)
            self._browser = future.result(timeout=30)
            console.success("Browser restarted successfully")

    async def _do_fetch(
        self,
        url: str,
        settle: float,
        headless: bool,
        proxy: str | None,
        snapshot: bool = False,
    ) -> tuple[bytes, int, bytes | None]:
        """
        Fetches data from a specified URL asynchronously, allowing for the use of a proxy, headless browser,
        and optional snapshot capture. Adjusts to settle time before retrieving the webpage content and status.

        Parameters:
            url (str): The URL to fetch data from.
            settle (float): The amount of time to wait before retrieving content.
            headless (bool): Whether to use a headless browser for the operation.
            proxy (str | None): The proxy server to use for the request, or None to not use a proxy.
            snapshot (bool): Optional; Defaults to False. Determines if a snapshot of the page should
                be captured.

        Returns:
            tuple[bytes, int, bytes | None]: A tuple containing the HTML content of the page in bytes,
            the HTTP status code as an integer, and optionally the snapshot data in bytes (or None
            if no snapshot is taken).
        """
        html: Any = ""
        status: Any = 200
        shot: bytes | None = None
        if proxy:
            _silence_browser()
            # Route through a local auth-injecting relay: Chrome honours the
            # browser-level --proxy-server flag (which create_context() inherits),
            # while the upstream credentials stay out of the browser. A per-context
            # proxy_server pointing at the relay does NOT route reliably here, and
            # create_context can't carry user:pass auth itself.
            relay_server, listen_port = await _start_proxy_relay(proxy)
            browser = await self._start_browser(
                headless,
                extra_args=[f"--proxy-server=http://127.0.0.1:{listen_port}"],
            )
            try:
                initial_tab = browser.main_tab
                tab = await browser.create_context()
                try:
                    await initial_tab.close()
                except Exception:
                    pass
                await tab.get(_splash_url())
                page = await tab.get(url)
                await page.wait()
                await _wait_for_content(page)
                await asyncio.sleep(settle)
                if await page.evaluate(_JS_IS_CHROME_ERROR):
                    raise StealthConnectionError(
                        f"Browser engine connection failed fetching {url!r}"
                    )
                html = await page.evaluate(_JS_HTML)
                status = await page.evaluate(_JS_STATUS)
                if snapshot:
                    shot = await _cdp_snapshot(page)
            finally:
                browser.stop()
                relay_server.close()
        else:
            assert self._tab_sem is not None
            async with self._tab_sem:
                page = await self._browser.get(url, new_tab=True)
                await page.wait()
                await _wait_for_content(page)
                await asyncio.sleep(settle)
                if await page.evaluate(_JS_IS_CHROME_ERROR):
                    try:
                        await page.close()
                    except Exception:
                        pass
                    raise StealthConnectionError(
                        f"Browser engine connection failed fetching {url!r}"
                    )
                html = await page.evaluate(_JS_HTML)
                status = await page.evaluate(_JS_STATUS)
                if snapshot:
                    shot = await _cdp_snapshot(page)
                try:
                    await page.close()
                except Exception:
                    pass

        return str(html).encode(errors="replace"), int(status), shot

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

            logger.debug(
                "Initializing browser engine (headless=%s & settle=%ss)",
                headless,
                settle,
            )

            body: bytes = b""
            status: int = 200
            shot: bytes | None = None

            if ctx.proxy:
                loop = _make_loop()
                try:
                    body, status, shot = loop.run_until_complete(
                        self._do_fetch(request.url, settle, headless, ctx.proxy, snap)
                    )
                finally:
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        for task in pending:
                            task.cancel()
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                    loop.close()
            else:
                self._ensure_browser(headless=headless)

                # Proactive restart every N requests to prevent Chrome memory bloat.
                with self._count_lock:
                    self._request_count += 1
                    should_restart = self._request_count >= config.get(
                        "BROWSER_RESTART_EVERY"
                    )
                    if should_restart:
                        self._request_count = 0

                if should_restart:
                    console.info(
                        f"Proactively restarting browser after {config.get('BROWSER_RESTART_EVERY')} requests"
                    )
                    self._reset_browser(headless, self._browser)

                for attempt in range(2):
                    try:
                        assert self._loop is not None
                        future = asyncio.run_coroutine_threadsafe(
                            self._do_fetch(request.url, settle, headless, None, snap),
                            self._loop,
                        )
                        body, status, shot = future.result(timeout=ctx.timeout)
                        break
                    except (ConnectionRefusedError, RuntimeError) as exc:
                        if attempt == 0 and _is_browser_crash(exc):
                            console.warning(f"Browser crashed, restarting: {exc}")
                            self._reset_browser(headless, self._browser)
                        else:
                            raise

            logger.debug(
                "Browser engine fetched %s  status=%s  size=%d bytes",
                request.url,
                status,
                len(body),
            )
            return StealthResponse(
                request=request,
                status=status,
                headers={"content-type": "text/html; charset=utf-8"},
                body=body,
                _meta={"snapshot_content": shot} if shot is not None else None,
                _flags=["browser"],
            )

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
