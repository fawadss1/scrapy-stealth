# Example spider

## Full demo

The complete working spider is in
[`examples/full_spider.py`](https://github.com/fawadss1/scrapy-stealth/blob/master/examples/full_spider.py).

It demonstrates:

- Middleware + `STEALTH_ENABLED` via `custom_settings` (`driver="auto"`, turbo first)
- Per-request `basic` / `browser` overrides
- POST with JSON body and custom headers
- Optional `@snapshot` decorator
- Ban detection, Smart Proxy Management telemetry, and stealth stats on close

```bash
# From a Scrapy project
scrapy crawl stealth_demo

# One-off
scrapy runspider examples/full_spider.py
```

## Minimal spider

```python
import scrapy


class ExampleSpider(scrapy.Spider):
    name = "example"

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
        },
        "STEALTH_ENABLED": True,
    }

    def start_requests(self):
        yield scrapy.Request("https://example.com")

    def parse(self, response):
        yield {"title": response.css("title::text").get(), "url": response.url}
```

## Performance tip

Use stealth selectively when you can:

- Faster crawling on simple pages (native Scrapy or HTTP drivers)
- Lower proxy cost
- Better success rate on protected pages when you enable stealth or `driver="auto"`

## Next

- [Quick start](quickstart.md)
- [Cookies & HTTP requests](../guides/cookies-and-requests.md)
- [Scrapy stats](../reference/stats.md)
