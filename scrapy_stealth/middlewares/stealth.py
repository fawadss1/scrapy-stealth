from __future__ import annotations

from typing import Any

from scrapy import signals
from scrapy.http import Request, Response

from ..config import config
from ..engines.browser import BrowserEngine
from ..manager import EngineManager
from ..strategies.fingerprint import ProfileRotator
from ..strategies.proxy import ProxyRotator
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
                    logger.error(
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
            logger.error(
                "snapshot=True requires driver='browser' but current driver is %r. "
                "Snapshot will be ignored.",
                driver or config.get("STEALTH_DRIVER"),
            )

        return await engine.fetch(request, spider)
