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

* 🧬 Browser-level impersonation (TLS + HTTP/2 fingerprints)
* 🔁 Smarter retry strategies
* 🌐 Proxy and fingerprint rotation
* 🛡️ Anti-bot detection

### Result

* Higher success rate
* Lower proxy cost
* More stable crawls

---

## 📊 Comparison

| Feature                      | scrapy-stealth | scrapy-playwright | scrapy-splash | scrapy-selenium | Scrapy (default) |
|------------------------------|:--------------:|:-----------------:|:-------------:|:---------------:|:----------------:|
| TLS fingerprint spoofing     |       ✅        |         ❌         |       ❌       |        ❌        |        ❌         |
| HTTP/2 support               |       ✅        |         ✅         |       ❌       |        ❌        |        ❌         |
| Browser impersonation        |       ✅        |    ⚠️ partial     |       ❌       |        ❌        |        ❌         |
| Proxy rotation (built-in)    |       ✅        |         ❌         |       ❌       |        ❌        |        ❌         |
| Fingerprint rotation         |       ✅        |         ❌         |       ❌       |        ❌        |        ❌         |
| Anti-bot detection           |       ✅        |         ❌         |       ❌       |        ❌        |        ❌         |
| Smart retry logic            |       ✅        |         ❌         |       ❌       |        ❌        |        ❌         |
| Per-request engine switching |       ✅        |         ❌         |       ❌       |        ❌        |        ❌         |
| Headless browser required    |       ❌        |         ✅         |       ✅       |        ✅        |        ❌         |
| JavaScript rendering         |       ❌        |         ✅         |       ✅       |        ✅        |        ❌         |
| Native Scrapy integration    |       ✅        |         ✅         |       ✅       |   ⚠️ partial    |        ✅         |
| Memory footprint             |     🟢 Low     |      🔴 High      |    🔴 High    |     🔴 High     |      🟢 Low      |

> ⚠️ `scrapy-playwright` passes real browser TLS but does not spoof fingerprint profiles like `scrapy-stealth` does.
> `scrapy-stealth` does **not** render JavaScript — use it for APIs and HTML pages that don't require a full browser.

---

## ✨ Features

* 🔌 Pluggable engine system (`scrapy`, `stealth`)
* 🧠 Per-request engine selection via `request.meta`
* 🌐 Proxy support and rotation
* 🧬 Browser fingerprint rotation
* 🔁 Smart retry logic
* 🛡️ Anti-bot detection (status + content-based, Cloudflare, Akamai)
* ⚡ Thread-safe async integration

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

## 🔧 Global Configuration

Customise package-wide defaults via the shared `config` instance.
All settings must be applied **at module level**, before the spider class — the engine client is
created at middleware initialisation, so changes inside `start_requests` or `parse` will have no effect.

```python
# myspider.py
import scrapy
from scrapy_stealth.config import config

config.DEFAULT_ENGINE  = "stealth"      # "scrapy" (native) or "stealth" (browser impersonation)
config.DEFAULT_PROFILE = "chrome_147"   # browser profile when meta["profile"] is not set
config.DEFAULT_TIMEOUT = 30             # stealth request timeout in seconds
config.HTTP2           = True           # False for servers that only support HTTP/1.1
config.BLOCK_CODES    |= {407}          # extend blocked status codes (|= keeps defaults)
config.BLOCK_KEYWORDS.append("banned")  # extend blocked body-text patterns


class MySpider(scrapy.Spider):
    name = "example"
    ...
```

```python
# ❌ wrong — too late, the engine client is already created
class MySpider(scrapy.Spider):
    def start_requests(self):
        config.HTTP2 = False  # has no effect
        ...
```

You can also read any value programmatically:

```python
config.get("DEFAULT_ENGINE")          # "scrapy"
config.get("MISSING_KEY", "default")  # "default"
```

| Attribute         | Type             | Default                           | Description                                                      |
|-------------------|------------------|-----------------------------------|------------------------------------------------------------------|
| `DEFAULT_ENGINE`  | `str`            | `"scrapy"`                        | Engine used when `request.meta["engine"]` is absent              |
| `DEFAULT_PROFILE` | `str`            | `"chrome_147"`                    | Browser profile used when none is specified                      |
| `DEFAULT_TIMEOUT` | `int`            | `30`                              | Request timeout in seconds                                       |
| `HTTP2`           | `bool`           | `True`                            | HTTP/2 mode; overridable per-request via `meta["http2"]`         |
| `BLOCK_CODES`     | `frozenset[int]` | `{403, 429, 503}`                 | HTTP status codes considered blocked                             |
| `BLOCK_KEYWORDS`  | `list[str]`      | `["captcha", "access denied", …]` | Body-text patterns considered blocked                            |

For one-off overrides on a single request, use `request.meta["http2"]` instead (see Per-Request Configuration below).

---

## ⚙️ Per-Request Configuration

All options are passed via `request.meta`:

| Key               | Type   | Description                                                  |
|-------------------|--------|--------------------------------------------------------------|
| `engine`          | `str`  | `"scrapy"` (default) or `"stealth"`                          |
| `profile`         | `str`  | Browser profile (e.g. `"chrome_147"`, `"safari_ios_18_1_1"`) |
| `proxy`           | `str`  | Explicit proxy URL                                           |
| `stealth_timeout` | `int`  | Per-request timeout in seconds (overrides default 30s)       |
| `http2`           | `bool` | `True` = HTTP/2, `False` = HTTP/1.1 (overrides `config.HTTP2` for this request) |
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