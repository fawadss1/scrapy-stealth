from __future__ import annotations

from typing import Any

from scrapy import signals
from scrapy.http import Request, Response
from twisted.internet.defer import Deferred

from ..constants import DEFAULT_ENGINE
from ..manager import EngineManager
from ..strategies.fingerprint import ProfileRotator
from ..strategies.proxy import ProxyRotator
from ..utils.logger import get_logger
from ..utils.meta import _get_meta_data, _is_meta_enabled

logger = get_logger()


class StealthDownloaderMiddleware:
    """Main middleware routing requests through stealth engines."""

    def __init__(self, proxies: list[str] | None = None) -> None:
        self.manager = EngineManager()
        self._proxy_rotator = ProxyRotator(proxies=proxies or [])
        self._profile_rotator = ProfileRotator()

    @classmethod
    def from_crawler(cls, crawler: Any) -> StealthDownloaderMiddleware:
        proxies = crawler.settings.getlist("STEALTH_PROXIES", [])
        mw = cls(proxies=proxies)
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        return mw

    def spider_opened(self, spider: Any) -> None:
        proxies = spider.crawler.settings.getlist("STEALTH_PROXIES", [])
        self._proxy_rotator = ProxyRotator(proxies=proxies)
        logger.debug("Loaded %d proxies from spider settings", len(proxies))

    def process_request(self, request: Request, spider: Any) -> Response | Deferred | None:
        if _is_meta_enabled(request, "rotate_profile"):
            request.meta.setdefault("impersonate", self._profile_rotator.get())
            logger.debug("Impersonate profile set to: %s", request.meta["impersonate"])

        if _is_meta_enabled(request, "rotate_proxy"):
            if not self._proxy_rotator.proxies:
                logger.error(
                    "rotate_proxy=True but STEALTH_PROXIES is not configured in settings. "
                    "Add STEALTH_PROXIES to your settings.py."
                )
            else:
                proxy = self._proxy_rotator.get()
                if proxy:
                    request.meta.setdefault("proxy", proxy)
                    logger.debug("Proxy set to: %s", request.meta["proxy"])

        engine_name = _get_meta_data(request, "engine", DEFAULT_ENGINE)
        engine = self.manager.get(engine_name)
        return engine.fetch(request, spider)
