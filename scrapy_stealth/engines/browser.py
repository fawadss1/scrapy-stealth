from __future__ import annotations

import asyncio
import sys
import threading
from typing import Any

from scrapy.http import Request, Response

from .base import BaseEngine
from ..config import config
from ..utils.logger import get_logger
from ..utils.meta import _get_meta_data
from ..utils.response import StealthResponse

logger = get_logger()

_BROWSER_ARGS: list[str] = [
    "--window-size=1366,768",
    "--window-position=0,0",
    "--disable-blink-features=AutomationControlled",
]

_JS_HTML = (
    "document.querySelector('.json-formatter-container')"
    " ? document.body.innerText"
    " : document.documentElement.innerHTML"
)
_JS_STATUS = "performance.getEntriesByType('navigation')[0]?.responseStatus ?? 200"


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
    import base64
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

    def _build_args(self, headless: bool) -> list[str]:
        args = list(_BROWSER_ARGS)
        if headless:
            args.append("--headless=new")
        return args

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
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
        import nodriver as _nd
        _silence_browser()
        return await _nd.start(browser_args=self._build_args(headless))

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
        shot: bytes | None = None
        if proxy:
            import nodriver as _nd
            _silence_browser()
            browser = await _nd.start(browser_args=self._build_args(headless))
            try:
                initial_tab = browser.main_tab
                tab = await browser.create_context(proxy_server=proxy)
                try:
                    await initial_tab.close()
                except Exception:
                    pass
                await tab.get(_splash_url())
                page = await tab.get(url)
                await asyncio.sleep(settle)
                html: Any = await page.evaluate(_JS_HTML)
                status: Any = await page.evaluate(_JS_STATUS)
                if snapshot:
                    shot = await _cdp_snapshot(page)
            finally:
                browser.stop()
        else:
            page = await self._browser.get(url)
            await asyncio.sleep(settle)
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
        try:
            ctx = self._ctx(request)
            headless: bool = _get_meta_data(request, "headless", config.get("BROWSER_HEADLESS"))
            settle: float = _get_meta_data(request, "settle", config.get("BROWSER_SETTLE_S"))
            snap: bool = _get_meta_data(request, "snapshot", False)

            logger.debug(
                "Initializing browser engine (headless=%s & settle=%ss)",
                headless, settle,
            )

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
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    loop.close()
            else:
                self._ensure_browser(headless=headless)
                assert self._loop is not None
                future = asyncio.run_coroutine_threadsafe(
                    self._do_fetch(request.url, settle, headless, None, snap), self._loop
                )
                body, status, shot = future.result(timeout=ctx.timeout)

            logger.debug(
                "Browser engine fetched %s  status=%s  size=%d bytes",
                request.url, status, len(body),
            )
            return StealthResponse(
                request=request,
                status=status,
                headers={"content-type": "text/html; charset=utf-8"},
                body=body,
                _meta={"snapshot_content": shot} if shot is not None else None,
            )

        except TimeoutError:
            raise
        except Exception as exc:
            logger.exception("Browser engine request failed: %s", exc)
            return None
