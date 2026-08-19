"""Full scrapy-stealth spider example.

Run from a Scrapy project after installing scrapy-stealth::

    scrapy crawl stealth_demo

Or as a one-off script::

    scrapy runspider examples/full_spider.py
"""

from __future__ import annotations

import json
from urllib.parse import urlencode

import scrapy

from scrapy_stealth.decorators import snapshot
from scrapy_stealth.detectors import AntiBotDetector


class StealthDemoSpider(scrapy.Spider):
    """Demonstrates global stealth settings + per-request driver overrides."""

    name = "stealth_demo"

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
        },
        # Route every request through stealth with driver="auto" (turbo first, browser on ban).
        "STEALTH_ENABLED": True,
        # Optional: seeded as engine default; rotated on ban-streak recycle.
        # "STEALTH_PROXIES": [
        #     "http://user:pass@proxy1:8080",
        #     "socks5://proxy2:1080",
        # ],
        # Optional: pin hosts to fixed origin IPs.
        # "STEALTH_DNS_OVERRIDES": {"example.com": "93.184.216.34"},
        "STEALTH_RECYCLE_AFTER_BANS": 5,
        "COOKIES_ENABLED": True,  # required for browser → turbo cookie jar handoff
        "BROWSER_HEADLESS": False,
        "BROWSER_SETTLE_S": 4.0,
        "BROWSER_STATIC_ASSETS_BLOCK": True,
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": False,
        "TELNETCONSOLE_ENABLED": False,
    }

    start_urls = [
        "https://example.com",
        "https://postman-echo.com/get",
    ]

    def start_requests(self):
        # 1) Default auto path (STEALTH_ENABLED injects driver="auto"; turbo runs first).
        yield scrapy.Request(
            self.start_urls[0],
            callback=self.parse,
            dont_filter=True,
        )

        # 2) Force basic for a lightweight GET.
        yield scrapy.Request(
            self.start_urls[1],
            callback=self.parse,
            meta={"stealth": {"driver": "basic"}},
            dont_filter=True,
        )

        # 3) JSON POST — same shape on basic, turbo, and browser.
        post_body = json.dumps({"search": "laptop", "page": 1}).encode()
        post_headers = {"Content-Type": "application/json"}
        for driver in ("basic", "turbo", "browser"):
            yield scrapy.Request(
                "https://postman-echo.com/post",
                method="POST",
                body=post_body,
                headers=post_headers,
                callback=self.parse_post_echo,
                meta={"stealth": {"driver": driver}},
                dont_filter=True,
            )

        # 4) Form POST login (browser) — quotes.toscrape tutorial site.
        yield scrapy.Request(
            "https://quotes.toscrape.com/login",
            method="POST",
            body=urlencode({"username": "admin", "password": "admin"}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            callback=self.parse_quotes_login,
            meta={"stealth": {"driver": "browser"}},
            dont_filter=True,
        )

        # 5) Real browser + snapshot for JS / challenge-heavy pages.
        yield scrapy.Request(
            self.start_urls[0],
            callback=self.parse_browser,
            meta={
                "stealth": {
                    "driver": "browser",
                    "settle": 3.0,
                    "snapshot": True,
                    "static_assets_block": False,  # keep assets for a real screenshot
                }
            },
            dont_filter=True,
        )

        # 6) Opt out of stealth for a specific request.
        # yield scrapy.Request(
        #     "https://postman-echo.com/get",
        #     callback=self.parse,
        #     meta={"stealth": False},
        # )

    def parse(self, response: scrapy.http.Response):
        detector = AntiBotDetector()
        if detector.is_blocked(response):
            self.logger.warning("Blocked response from %s", response.url)
            return

        yield {
            "url": response.url,
            "status": response.status,
            "title": response.css("title::text").get(),
            "driver": response.flags,
            "bytes": len(response.body),
        }

    def parse_post_echo(self, response: scrapy.http.Response):
        """postman-echo.com/post returns JSON echoing the request body."""
        try:
            payload = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error(
                "Non-JSON echo from %s: %s", response.url, response.text[:200]
            )
            return

        data = payload.get("data")
        yield {
            "url": response.url,
            "status": response.status,
            "driver": response.flags,
            "echo_data": data,
            "content_type_sent": (payload.get("headers") or {}).get("content-type"),
        }

    def parse_quotes_login(self, response: scrapy.http.Response):
        logged_in = "Logout" in response.text
        yield {
            "url": response.url,
            "status": response.status,
            "driver": response.flags,
            "logged_in": logged_in,
            "title": response.css("title::text").get(),
        }

        if not logged_in:
            return

        # Cookie handoff: browser session → turbo (via Scrapy cookie jar + COOKIES_ENABLED)
        yield scrapy.Request(
            "https://quotes.toscrape.com/",
            meta={"stealth": {"driver": "turbo"}},
            callback=self.parse_quotes_home,
            dont_filter=True,
        )

    def parse_quotes_home(self, response: scrapy.http.Response):
        yield {
            "url": response.url,
            "status": response.status,
            "driver": response.flags,
            "logged_in_after_turbo": "Logout" in response.text,
        }

    @snapshot  # saves PNG under stealth_snapshots/ when snapshot=True was set
    def parse_browser(self, response: scrapy.http.Response):
        yield {
            "url": response.url,
            "status": response.status,
            "title": response.css("title::text").get(),
            "driver": response.flags,
            "has_snapshot": bool(response.meta.get("snapshot_content")),
        }

    def closed(self, reason: str):
        stats = self.crawler.stats.get_stats()
        self.logger.info(
            "Done (%s) — requests=%s successes=%s bans=%s recycles=%s driver=%s",
            reason,
            stats.get("stealth/requests"),
            stats.get("stealth/successes"),
            stats.get("stealth/bans"),
            stats.get("stealth/recycles"),
            stats.get("stealth/driver"),
        )
