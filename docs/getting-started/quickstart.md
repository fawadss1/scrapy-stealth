# Quick start

## Recommended setup

Two settings — smart by default:

```python
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
}
STEALTH_ENABLED = True
```

This runs **`turbo`** first (deep TLS fingerprinting), then retries once with **visible Chrome**
when a JS challenge or session ban is detected.

## Global mode (`STEALTH_ENABLED = True`)

```python
# settings.py or spider custom_settings
STEALTH_ENABLED = True

# In the spider — no meta needed
yield scrapy.Request("https://example.com")

# Opt out for one request
yield scrapy.Request("https://api.internal/health", meta={"stealth": False})

# Force HTTP-only (no browser fallback)
yield scrapy.Request(
    "https://example.com",
    meta={"stealth": {"driver": "turbo"}},
)
```

## Per-request mode

Activate stealth only on specific URLs:

```python
yield scrapy.Request(
    "https://example.com",
    meta={"stealth": {"driver": "auto"}},
)

yield scrapy.Request(
    "https://example.com",
    meta={"stealth": {"driver": "turbo"}},
)
```

## Spider `custom_settings` example

```python
class MySpider(scrapy.Spider):
    name = "example"

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
        },
        "STEALTH_ENABLED": True,
        "STEALTH_PROXIES": [
            "http://proxy1:8080",
            "http://user:pass@proxy2:8080",
        ],
        "STEALTH_DNS_OVERRIDES": {
            "example.com": "203.0.113.10",
        },
    }

    def start_requests(self):
        yield scrapy.Request("https://example.com", callback=self.parse)

    def parse(self, response):
        yield {"title": response.css("title::text").get()}
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
        yield {"url": response.url}
```

## Run the demo spider

```bash
scrapy runspider examples/full_spider.py
```

## Next

- [Global settings](../configuration/settings.md)
- [Per-request meta](../configuration/meta.md)
- [Smart selection (`auto`)](../drivers/auto.md)
