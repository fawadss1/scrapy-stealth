<p align="center">
  <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/logo.png" alt="scrapy-stealth logo" width="925"/>
</p>

<h1 align="center">scrapy-stealth</h1>

<p align="center"><strong>Stealthy Crawling. Maximum Results.</strong></p>

<p align="center">A pluggable anti-bot and stealth framework for Scrapy.</p>

[![PyPI version](https://img.shields.io/pypi/v/scrapy-stealth?color=blue)](https://pypi.org/project/scrapy-stealth/)
[![Python versions](https://img.shields.io/pypi/pyversions/scrapy-stealth)](https://pypi.org/project/scrapy-stealth/)
[![Downloads](https://img.shields.io/pypi/dm/scrapy-stealth)](https://pypi.org/project/scrapy-stealth/)
[![GitHub release](https://img.shields.io/github/v/release/fawadss1/scrapy-stealth)](https://github.com/fawadss1/scrapy-stealth/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/fawadss1/scrapy-stealth/blob/master/LICENSE)
[![Changelog](https://img.shields.io/badge/changelog-releases-informational)](https://github.com/fawadss1/scrapy-stealth/releases)

`scrapy-stealth` extends Scrapy with browser impersonation, proxy rotation, fingerprint cycling, and intelligent retry strategies —
designed for large-scale, production-grade crawling.

---

## 🧠 Why scrapy-stealth?

Scrapy is fast and powerful, but modern websites use advanced anti-bot protections such as:

* TLS fingerprinting
* Browser behavior detection
* Rate limiting and IP blocking

`scrapy-stealth` helps by adding:

* 🧬 Browser-level impersonation (TLS + HTTP2 fingerprints)
* 🔁 Smarter retry strategies
* 🌐 Proxy and fingerprint rotation
* 🛡️ Anti-bot detection

### Result

* Higher success rate
* Lower proxy cost
* More stable crawls

---

## ✨ Features

* 🔌 Pluggable engine system (`scrapy`, `stealth`)
* 🧠 Per-request engine selection via `request.meta`
* 🌐 Proxy support and rotation
* 🧬 Browser fingerprint rotation
* 🔁 Smart retry logic (manual integration)
* 🛡️ Anti-bot detection (status + content-based)
* ⚡ Thread-safe async integration
* Advanced anti-bot detection (Cloudflare, Akamai)

---

## 📦 Installation

```bash
pip install scrapy-stealth
```

> Requires Python 3.10+ and Scrapy 2.15+

---

## ⚙️ Setup

### Option 1 — Global (`settings.py`)

```python
# 1. Enable the middleware
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.stealth.StealthDownloaderMiddleware": 950,
}

# 2. (Optional) Proxy list for automatic rotation
#    Used when request.meta["rotate_proxy"] = True
#    Supported schemes: http, https, socks4, socks5
#    Each entry must include a scheme and port
STEALTH_PROXIES = [
    "http://proxy1:8080",
    "http://proxy2:8080",
    "http://user:pass@proxy3:8080",  # with authentication
    "socks5://proxy4:1080",
]
```

### Option 2 — Per-spider (`custom_settings`)

Configure the middleware and proxies directly on the spider — no changes to `settings.py` required.
Each spider can have its own independent proxy list.

```python
class MySpider(scrapy.Spider):
    name = "example"

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_stealth.middlewares.stealth.StealthDownloaderMiddleware": 950,
        },
        "STEALTH_PROXIES": [
            "http://proxy1:8080",
            "http://user:pass@proxy2:8080",
            "socks5://proxy3:1080",
        ],
    }
```

> Proxies are validated at startup — invalid format or unsupported scheme raises `ValueError` immediately.

---

## 🚀 Quick Start

```python
yield scrapy.Request(
    url="https://example.com",
    meta={
        "engine": "stealth",
    },
)
```

---

## ⚙️ Per-Request Configuration

All options are passed via `request.meta`:

| Key               | Type   | Description                                                  |
|-------------------|--------|--------------------------------------------------------------|
| `engine`          | `str`  | `"scrapy"` (default) or `"stealth"`                          |
| `profile`         | `str`  | Browser profile (e.g. `"chrome_147"`, `"safari_ios_18_1_1"`) |
| `proxy`           | `str`  | Explicit proxy URL                                           |
| `stealth_timeout` | `int`  | Per-request timeout in seconds (overrides default 30s)       |
| `rotate_proxy`    | `bool` | Auto-pick a proxy from `STEALTH_PROXIES`                     |
| `rotate_profile`  | `bool` | Auto-pick a random browser profile                           |

---

## 🔁 Automatic Rotation

```python
yield scrapy.Request(
    url,
    meta={
        "engine": "stealth",
        "rotate_proxy": True,
        "rotate_profile": True,
    },
)
```

---

## 🧩 Strategies

### Proxy Rotation

```python
from scrapy_stealth.strategies.proxy import ProxyRotator

proxy_rotator = ProxyRotator([
    "http://proxy1:8080",
    "http://proxy2:8080",
])

yield scrapy.Request(
    url,
    meta={
        "engine": "stealth",
        "proxy": proxy_rotator.get(),
    },
)
```

---

### Fingerprint Rotation

```python
from scrapy_stealth.strategies.fingerprint import ProfileRotator

fp = ProfileRotator()

yield scrapy.Request(
    url,
    meta={
        "engine": "stealth",
        "profile": fp.get(),
    },
)
```

---

### Intelligent Retry

```python
from scrapy_stealth.strategies.retry import RetryHandler

retry = RetryHandler()


def parse(self, response):
    if retry.should_retry(response):
        yield retry.build(response.request)
        return
```

---

## 🛡️ Anti-Bot Detection

```python
from scrapy_stealth.detectors.antibot import AntiBotDetector

detector = AntiBotDetector()

if detector.is_blocked(response):
    print("Blocked!")
```

---

## 📊 Example

```python
import scrapy


class ExampleSpider(scrapy.Spider):
    name = "example"

    def start_requests(self):
        yield scrapy.Request(
            "https://example.com",
            meta={
                "engine": "stealth",
                "rotate_proxy": True,
                "rotate_profile": True,
            },
        )

    def parse(self, response):
        yield {
            "title": response.css("title::text").get(),
            "url": response.url,
        }
```

---

## ⚡ Performance Insight

Using stealth selectively:

* ⚡ Faster crawling (Scrapy for simple pages)
* 💰 Lower proxy cost
* 🛡️ Better success rate on protected pages
---

## 📜 Changelog

See [CHANGELOG.md](https://github.com/fawadss1/scrapy-stealth/blob/master/CHANGELOG.md) for a full history of changes, or browse [GitHub Releases](https://github.com/fawadss1/scrapy-stealth/releases).

---

## 🤝 Contributing

See [CONTRIBUTING.md](https://github.com/fawadss1/scrapy-stealth/blob/master/CONTRIBUTING.md) for guidelines on how to contribute.

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute.
See [LICENSE](https://github.com/fawadss1/scrapy-stealth/blob/master/LICENSE) for the full text.