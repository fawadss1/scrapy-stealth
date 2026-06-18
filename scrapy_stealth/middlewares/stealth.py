from __future__ import annotations

from typing import Any

from scrapy import signals
from scrapy.http import Request, Response

from ..config import config
from ..engines.browser import BrowserEngine
from ..manager import EngineManager
from ..strategies.fingerprint import ProfileRotator
from ..strategies.proxy import ProxyRotator
from ..utils.console import console
from ..utils.logger import get_logger
from ..utils.meta import (
    STEALTH_KEY,
    _get_meta_data,
    _is_meta_enabled,
    _resolve_engine,
)

logger = get_logger()


class StealthDownloaderMiddleware:
    """Main middleware routing requests through stealth engines."""

    def __init__(
        self, proxies: list[str] | None = None, stealth_enabled: bool = False
    ) -> None:
        self.manager = EngineManager()
        self._proxy_rotator = ProxyRotator(proxies=proxies or [])
        self._profile_rotator = ProfileRotator()
        self._stealth_enabled = stealth_enabled

    @classmethod
    def from_crawler(cls, crawler: Any) -> StealthDownloaderMiddleware:
        proxies = crawler.settings.getlist("STEALTH_PROXIES", [])
        stealth_enabled = crawler.settings.getbool("STEALTH_ENABLED", False)
        mw = cls(proxies=proxies, stealth_enabled=stealth_enabled)
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        return mw

    def spider_opened(self, spider: Any) -> None:
        settings = spider.crawler.settings
        proxies = settings.getlist("STEALTH_PROXIES", [])
        self._proxy_rotator = ProxyRotator(proxies=proxies)
        self._stealth_enabled = settings.getbool(
            "STEALTH_ENABLED", self._stealth_enabled
        )
        if driver := settings.get("STEALTH_DRIVER"):
            config.STEALTH_DRIVER = driver
        if (no_sandbox := settings.get("BROWSER_NO_SANDBOX")) is not None:
            config.BROWSER_NO_SANDBOX = no_sandbox
        if (executable_path := settings.get("BROWSER_EXECUTABLE_PATH")) is not None:
            config.BROWSER_EXECUTABLE_PATH = executable_path
        if (assets_block := settings.get("BROWSER_STATIC_ASSETS_BLOCK")) is not None:
            config.BROWSER_STATIC_ASSETS_BLOCK = bool(assets_block)
        logger.debug("Loaded %d proxies from spider settings", len(proxies))

    async def process_request(self, request: Request, spider: Any) -> Response | None:
        if self._stealth_enabled and STEALTH_KEY not in request.meta:
            request.meta[STEALTH_KEY] = {}

        engine_name = _resolve_engine(request, config.get("DEFAULT_ENGINE"))

        if engine_name == "stealth":
            stealth_meta = request.meta.setdefault(STEALTH_KEY, {})

            if _is_meta_enabled(request, "rotate_profile"):
                stealth_meta.setdefault("profile", self._profile_rotator.get())
                logger.debug("Profile set to: %s", stealth_meta["profile"])

            if _is_meta_enabled(request, "rotate_proxy"):
                if not self._proxy_rotator.proxies:
                    console.error(
                        "rotate_proxy=True but STEALTH_PROXIES is not configured in settings. "
                        "Add STEALTH_PROXIES to your settings.py."
                    )
                else:
                    proxy = self._proxy_rotator.get()
                    if proxy:
                        stealth_meta.setdefault("proxy", proxy)
                        logger.debug("Proxy set to: %s", stealth_meta["proxy"])

        driver = _get_meta_data(request, "driver")
        engine = self.manager.get(engine_name, driver)

        if _get_meta_data(request, "snapshot", False) and not isinstance(
            engine, BrowserEngine
        ):
            console.warning(
                f"snapshot=True requires driver='browser' but current driver is "
                f"{(driver or config.get('STEALTH_DRIVER'))!r}. Snapshot will be ignored."
            )

        return await engine.fetch(request, spider)
