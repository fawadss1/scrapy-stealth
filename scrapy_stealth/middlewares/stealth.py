from __future__ import annotations

from typing import Any

from scrapy import signals
from scrapy.http import Request, Response

from ..config import config
from ..engines.browser import BrowserEngine
from ..manager import EngineManager
from ..strategies.proxy import ProxyRotator
from ..utils.console import console
from ..utils.dns import validate_dns_overrides
from ..utils.logger import get_logger
from ..utils.meta import STEALTH_KEY, _get_meta_data, _resolve_engine
from ..utils.stats import StealthStats
from ..utils.updates import update_available

logger = get_logger()


class StealthDownloaderMiddleware:
    """Main middleware routing requests through stealth engines."""

    def __init__(
        self,
        proxies: list[str] | None = None,
        stealth_enabled: bool = False,
        crawler: Any | None = None,
    ) -> None:
        self.manager = EngineManager()
        self._proxy_rotator = ProxyRotator(proxies=proxies or [])
        self._stealth_enabled = stealth_enabled
        self._crawler = crawler
        self._stealth_stats = StealthStats(
            crawler.stats if crawler is not None else None
        )

    @classmethod
    def from_crawler(cls, crawler: Any) -> StealthDownloaderMiddleware:
        proxies = crawler.settings.getlist("STEALTH_PROXIES", [])
        stealth_enabled = crawler.settings.getbool("STEALTH_ENABLED", False)
        mw = cls(proxies=proxies, stealth_enabled=stealth_enabled, crawler=crawler)
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(mw.spider_closed, signal=signals.spider_closed)
        update_available()
        return mw

    def spider_closed(self, spider: Any) -> None:
        self.manager.close()

    def spider_opened(self, spider: Any) -> None:
        settings = spider.crawler.settings
        proxies = settings.getlist("STEALTH_PROXIES", [])
        self._proxy_rotator = ProxyRotator(proxies=proxies)
        config.STEALTH_PROXIES = list(self._proxy_rotator.proxies)
        self.manager.seed_proxies()
        stats = spider.crawler.stats
        self._stealth_stats = StealthStats(stats)
        self.manager.set_stats(stats)
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
        if settings.get("BROWSER_PROXY_BYPASS_LIST") is not None:
            config.BROWSER_PROXY_BYPASS_LIST = settings.getlist(
                "BROWSER_PROXY_BYPASS_LIST"
            )
        dns_setting = settings.get("STEALTH_DNS_OVERRIDES")
        if isinstance(dns_setting, dict):
            config.STEALTH_DNS_OVERRIDES = validate_dns_overrides(dns_setting)
            logger.debug(
                "Loaded %d DNS overrides from spider settings",
                len(config.STEALTH_DNS_OVERRIDES),
            )
        logger.debug("Loaded %d proxies from spider settings", len(proxies))

    @property
    def _spider(self) -> Any:
        """Active spider from the crawler saved in ``from_crawler``."""
        if self._crawler is None:
            return None
        return getattr(self._crawler, "spider", None)

    async def process_request(self, request: Request) -> Response | None:
        if self._stealth_enabled and STEALTH_KEY not in request.meta:
            request.meta[STEALTH_KEY] = {}

        engine_name = _resolve_engine(request, config.get("DEFAULT_ENGINE"))
        driver = _get_meta_data(request, "driver")
        engine = self.manager.get(engine_name, driver)

        if engine_name == "stealth":
            driver_label = getattr(engine, "driver_name", None)
            if not isinstance(driver_label, str):
                driver_label = config.get("STEALTH_DRIVER") or "basic"
            self._stealth_stats.record_request(driver_label)

        if _get_meta_data(request, "snapshot", False) and not isinstance(
            engine, BrowserEngine
        ):
            console.warning(
                f"snapshot=True requires driver='browser' but current driver is "
                f"{(driver or config.get('STEALTH_DRIVER'))!r}. Snapshot will be ignored."
            )

        return await engine.fetch(request, self._spider)
