# scrapy-stealth

A pluggable anti-bot and stealth framework for Scrapy.

[![Changelog](https://img.shields.io/badge/changelog-releases-blue)](https://github.com/fawadss1/scrapy-stealth/releases)

`scrapy-stealth` extends Scrapy with browser impersonation, proxy rotation, fingerprint cycling, and intelligent retry strategies — built for large-scale, production-grade crawling.

---

## Features

- Pluggable engine system (`scrapy`, `stealth`, or custom)
- Browser impersonation (Chrome, Firefox, Safari, Edge, Opera — latest versions)
- Per-request engine selection via `request.meta`
- Proxy support and rotation
- Browser fingerprint rotation
- Smart retry logic that auto-escalates to stealth engine on block
- Anti-bot detection (403/429 status codes + content keyword matching)
- Thread-safe async integration

---

## Installation

```bash
pip install scrapy-stealth
```

> Requires Python 3.10+ and Scrapy 2.15+

---

## Quick Start

### 1. Enable the middleware in `settings.py`

```python
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.stealth.StealthDownloaderMiddleware": 950,
}
```

### 2. Use it in your spider

By default, requests go through the standard Scrapy engine. To use the stealth engine, set `engine` in `request.meta`:

```python
import scrapy

class MySpider(scrapy.Spider):
    name = "example"
    start_urls = ["https://example.com"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={"engine": "stealth"},
            )

    def parse(self, response):
        self.logger.info(f"Status: {response.status}")
        yield {"title": response.css("title::text").get()}
```

---

## Per-Request Configuration

All stealth options are set via `request.meta`:

| Key | Type | Description |
|---|---|---|
| `engine` | `str` | Engine to use: `"scrapy"` (default) or `"stealth"` |
| `impersonate` | `str` | Browser to impersonate: `"chrome_137"`, `"firefox_139"`, `"safari_18_5"`, etc. |
| `proxy` | `str` | Proxy URL, e.g. `"http://user:pass@host:port"` |

### Example with all options

```python
yield scrapy.Request(
    url="https://example.com",
    meta={
        "engine": "stealth",
        "impersonate": "firefox_139",
        "proxy": "http://user:pass@proxy-host:8080",
    },
)
```

---

## Strategies

### Proxy Rotation

Use `ProxyRotator` to randomly rotate proxies across requests:

```python
from scrapy_stealth.strategies.proxy import ProxyRotator

proxy_strategy = ProxyRotator(proxies=[
    "http://proxy1:8080",
    "http://proxy2:8080",
    "http://proxy3:8080",
])

yield scrapy.Request(
    url="https://example.com",
    meta={
        "engine": "stealth",
        "proxy": proxy_strategy.get(),
    },
)
```

### Fingerprint Rotation

Use `ProfileRotator` to randomly rotate the browser fingerprint:

```python
from scrapy_stealth.strategies.fingerprint import ProfileRotator

fp = ProfileRotator()

yield scrapy.Request(
    url="https://example.com",
    meta={
        "engine": "stealth",
        "impersonate": fp.get(),  # randomly picks from latest Chrome, Firefox, Safari, Edge, Opera
    },
)
```

### Intelligent Retry

Use `RetryHandler` in your spider or middleware to retry blocked responses with automatic engine escalation:

```python
from scrapy_stealth.strategies.retry import RetryHandler

retry = RetryHandler()

def parse(self, response):
    if retry.should_retry(response):  # triggers on 403, 429, 503
        yield retry.build(response.request)  # retries via stealth engine
        return
    # normal parsing ...
```

`build` automatically:
- Increments `retry_times` in meta
- Switches `engine` to `"stealth"`
- Sets `dont_filter=True` to bypass Scrapy's duplicate filter

---

## Anti-Bot Detection

Use `AntiBotDetector` to classify responses as blocked:

```python
from scrapy_stealth.detectors.antibot import AntiBotDetector

detector = AntiBotDetector()

def parse(self, response):
    if detector.is_blocked(response):
        self.logger.warning("Blocked! Retrying...")
        # handle retry ...
        return
    # normal parsing ...
```

Detects blocks via:
- HTTP status codes: `403`, `429`
- Body keywords: `"captcha"`, `"access denied"`, `"verify you are human"`

---

## Full Example Spider

```python
import scrapy
from scrapy_stealth.strategies.proxy import ProxyRotator
from scrapy_stealth.strategies.fingerprint import ProfileRotator
from scrapy_stealth.strategies.retry import RetryHandler
from scrapy_stealth.detectors.antibot import AntiBotDetector

proxy_rotator = ProxyRotator(proxies=[
    "http://proxy1:8080",
    "http://proxy2:8080",
])
fp_rotator = ProfileRotator()
retry_handler = RetryHandler()
detector = AntiBotDetector()


class StealthSpider(scrapy.Spider):
    name = "stealth_example"
    start_urls = ["https://example.com"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "engine": "stealth",
                    "impersonate": fp_rotator.get(),
                    "proxy": proxy_rotator.get(),
                },
            )

    def parse(self, response):
        if detector.is_blocked(response):
            self.logger.warning("Blocked response detected, retrying...")
            yield retry_handler.build(response.request)
            return

        yield {"title": response.css("title::text").get(), "url": response.url}
```

---

## Supported Browsers for Impersonation

| Value | Browser |
|---|---|
| `chrome_137` | Chrome 137 (default) |
| `chrome_136` | Chrome 136 |
| `chrome_135` | Chrome 135 |
| `chrome_134` | Chrome 134 |
| `chrome_133` | Chrome 133 |
| `chrome_132` | Chrome 132 |
| `chrome_131` | Chrome 131 |
| `chrome_130` | Chrome 130 |
| `chrome_129` | Chrome 129 |
| `firefox_139` | Firefox 139 |
| `firefox_136` | Firefox 136 |
| `firefox_135` | Firefox 135 |
| `firefox_133` | Firefox 133 |
| `firefox_private_136` | Firefox 136 Private/Incognito |
| `firefox_private_135` | Firefox 135 Private/Incognito |
| `firefox_android_135` | Firefox Android 135 |
| `safari_18_5` | Safari 18.5 |
| `safari_18_3_1` | Safari 18.3.1 |
| `safari_18_3` | Safari 18.3 |
| `safari_18_2` | Safari 18.2 |
| `safari_18` | Safari 18 |
| `safari_ios_18_1_1` | Safari iOS 18.1.1 |
| `safari_ios_17_4_1` | Safari iOS 17.4.1 |
| `safari_ios_17_2` | Safari iOS 17.2 |
| `safari_ipad_18` | Safari iPad 18 |
| `edge_134` | Edge 134 |
| `edge_131` | Edge 131 |
| `edge_127` | Edge 127 |
| `edge_122` | Edge 122 |
| `opera_119` | Opera 119 |
| `opera_118` | Opera 118 |
| `opera_117` | Opera 117 |
| `opera_116` | Opera 116 |
| `okhttp_5` | OkHttp 5 (Android app) |
| `okhttp_4_12` | OkHttp 4.12 (Android app) |
| `okhttp_4_10` | OkHttp 4.10 (Android app) |
| `okhttp_4_9` | OkHttp 4.9 (Android app) |
| `okhttp_3_14` | OkHttp 3.14 (Android app) |
| `okhttp_3_13` | OkHttp 3.13 (Android app) |
| `okhttp_3_11` | OkHttp 3.11 (Android app) |
| `okhttp_3_9` | OkHttp 3.9 (Android app) |

---

## Requirements

- Python 3.10+
- `scrapy >= 2.15.0`

---

## Contributing

Contributions are welcome! This is an open source project and all help is appreciated.

1. Fork the repository on [GitHub](https://github.com/fawadss1/scrapy-stealth)
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests if applicable
4. Open a pull request describing what you changed and why

**Ways to contribute:**
- Report bugs via [GitHub Issues](https://github.com/fawadss1/scrapy-stealth/issues)
- Suggest new engines, strategies, or detectors
- Improve documentation or examples
- Add support for new browser fingerprints

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a full history of changes, or browse [GitHub Releases](https://github.com/fawadss1/scrapy-stealth/releases).

---

## License

This project is licensed under the **MIT License** — free to use, modify, and distribute.
See [LICENSE](LICENSE) for the full text.
