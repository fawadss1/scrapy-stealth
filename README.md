<p align="center">
  <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/logo.png" alt="scrapy-stealth logo" width="925"/>
</p>

<h1 align="center">scrapy-stealth</h1>

<p align="center"><strong>Stealthy Crawling. Maximum Results.</strong></p>

<p align="center">A pluggable anti-bot and stealth framework for Scrapy.</p>

[![PyPI version](https://img.shields.io/pypi/v/scrapy-stealth?color=blue)](https://pypi.org/project/scrapy-stealth/)
[![Python versions](https://img.shields.io/pypi/pyversions/scrapy-stealth)](https://pypi.org/project/scrapy-stealth/)
[![Downloads](https://static.pepy.tech/badge/scrapy-stealth)](https://pepy.tech/project/scrapy-stealth)
[![GitHub release](https://img.shields.io/github/v/release/Suvastutech-Ltd/scrapy-stealth)](https://github.com/Suvastutech-Ltd/scrapy-stealth/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/fawadss1/scrapy-stealth/blob/master/LICENSE)
[![Changelog](https://img.shields.io/badge/changelog-releases-informational)](https://github.com/fawadss1/scrapy-stealth/releases)

`scrapy-stealth` extends Scrapy with browser impersonation, proxy rotation, fingerprint cycling, and intelligent retry strategies —
designed for large-scale, production-grade crawling.

---

## 💜 Sponsor

<table>
  <tr>
    <td width="380" align="center">
      <a href="https://go.nodemaven.com/Fawadss1readme">
        <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/sponsors/banner.svg" alt="NodeMaven" width="380"/>
      </a>
    </td>
    <td>
      <strong><a href="https://go.nodemaven.com/Fawadss1readme">NodeMaven</a></strong> — the most reliable proxy provider with the highest-quality IP on the market.
      Best solution for automation, web scraping, SEO research, and social media management.
      <br/><br/>
      <strong>Why NodeMaven?</strong>
      <ul>
        <li>99.9% uptime</li>
        <li>Sticky sessions up to 7 days</li>
        <li>IP filtering: all proxies have fraud score &lt;97%</li>
        <li>No KYC required</li>
        <li>Cashback on traffic — burn GB and earn up to 10% back</li>
      </ul>
      Special codes for scrapy-stealth users:
      <code>SCRAPYSTEALTH35</code> — 35% off Mobile and Residential Proxies;
      <code>SCRAPYSTEALTH40</code> — 40% off ISP (Static) Proxies.
    </td>
  </tr>
</table>

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

| Feature                      | scrapy-stealth | scrapy-impersonate | scrapy-playwright | scrapy-splash | Scrapy (default) |
|------------------------------|:--------------:|:------------------:|:-----------------:|:-------------:|:----------------:|
| TLS fingerprint spoofing     |       ✅        |         ✅          |         ❌         |       ❌       |        ❌         |
| HTTP/2 support               |       ✅        |         ✅          |         ✅         |       ❌       |        ❌         |
| Browser impersonation        |       ✅        |         ✅          |    ⚠️ partial     |       ❌       |        ❌         |
| Proxy rotation (built-in)    |       ✅        |         ❌          |         ❌         |       ❌       |        ❌         |
| Fingerprint rotation         |       ✅        |         ❌          |         ❌         |       ❌       |        ❌         |
| Anti-bot detection           |       ✅        |         ❌          |         ❌         |       ❌       |        ❌         |
| Smart retry logic            |       ✅        |         ❌          |         ❌         |       ❌       |        ❌         |
| Per-request engine switching |       ✅        |         ❌          |         ❌         |       ❌       |        ❌         |
| Headless browser required    |       ✅        |         ❌          |         ✅         |       ✅       |        ❌         |
| JavaScript rendering         |       ️✅       |         ❌          |         ✅         |       ✅       |        ❌         |
| Screenshot / snapshot        |       ✅        |         ❌          |         ✅         |       ✅       |        ❌         |
| Native Scrapy integration    |       ✅        |         ✅          |         ✅         |       ✅       |        ✅         |
| Memory footprint             |     🟢 Low     |       🟢 Low       |      🔴 High      |    🔴 High    |      🟢 Low      |

> ⚠️ `scrapy-playwright` passes real browser TLS but does not spoof fingerprint profiles like `scrapy-stealth` does.
> `scrapy-impersonate` provides TLS/HTTP2 impersonation via `curl_cffi` but lacks built-in rotation, detection, or per-request engine
> switching.
> JavaScript rendering is available via the optional `browser` driver — use it selectively for pages that require a full browser.

---

## ✨ Features

* 🔌 Pluggable engine system (`scrapy`, `stealth`)
* 🧠 Per-request engine selection via `request.meta`
* 🌐 Proxy support and rotation
* 🧬 Browser fingerprint rotation
* 🔁 Smart retry logic
* 🛡️ Anti-bot detection (status + content-based, Cloudflare, Akamai)
* ⚡ Thread-safe async integration
* 🖥️ Real-browser engine (CDP) for JS-heavy pages
* 🔄 Intelligent browser restart — restarts on consecutive bans, not a fixed request count
* 🚫 Static asset blocking — skip images, fonts, CSS, and media for faster, lighter browser fetches
* 🎯 Proxy bypass list — send chosen domains straight to the origin instead of through the proxy (`--proxy-bypass-list`)
* 📸 Built-in snapshot decorator (`scrapy_stealth.decorators.snapshot`)

---

## 📦 Installation

```bash
pip install scrapy-stealth
```

> Requires Python 3.11+ and Scrapy 2.12–2.x

---

## ⚙️ Setup

### Option 1 — Global (`settings.py`)

```python
# 1. Enable the middleware
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
}

# 2. (Optional) Route ALL requests through stealth automatically — no meta needed per request
STEALTH_ENABLED = True
STEALTH_DRIVER = "turbo"  # "basic" (default), "turbo", or "browser"

# 3. (Optional) Proxy list for automatic rotation
#    Used when rotate_proxy=True (per-request) or when STEALTH_ENABLED=True with rotate_proxy
#    Supported schemes: http, https, socks4, socks5
STEALTH_PROXIES = [
    "http://proxy1:8080",
    "http://proxy2:8080",
    "http://user:pass@proxy3:8080",  # with authentication
    "socks5://proxy4:1080",
]
```

### Option 2 — Per-spider (`custom_settings`)

Configure the middleware and all stealth settings directly on the spider — no changes to `settings.py` required.

```python
class MySpider(scrapy.Spider):
    name = "example"

    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
        },
        "STEALTH_ENABLED": True,
        "STEALTH_DRIVER": "turbo",
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

**Option A — Per-request** (stealth only on specific requests):

```python
yield scrapy.Request(
    url="https://example.com",
    meta={"stealth": {}},
)
```

**Option B — Global mode** (stealth on every request automatically):

```python
# settings.py or custom_settings
STEALTH_ENABLED = True
STEALTH_DRIVER = "turbo"
```

```python
# No meta needed — all requests go through stealth
yield scrapy.Request(url="https://example.com")

# Opt out for a specific request
yield scrapy.Request(url="https://api.internal/health", meta={"stealth": False})
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

config.DEFAULT_ENGINE = "stealth"  # "scrapy" (native) or "stealth" (browser impersonation)
config.DEFAULT_PROFILE = "chrome_147"  # browser profile when meta["stealth"]["profile"] is not set
config.DEFAULT_TIMEOUT = 30  # stealth request timeout in seconds
config.STEALTH_DRIVER = "turbo"  # "basic" (default), "turbo", or "browser"
config.HTTP2 = True  # False for servers that only support HTTP/1.1
config.BLOCK_CODES |= {407}  # extend blocked status codes (|= keeps defaults)
config.BLOCK_KEYWORDS.append("banned")  # extend blocked body-text patterns
config.BROWSER_HEADLESS = True  # browser driver: headless mode (False = visible window, more stealthy)
config.BROWSER_SETTLE_S = 4.0  # browser driver: seconds to wait after navigation for JS to finish
config.BROWSER_EXECUTABLE_PATH = "/usr/bin/brave-browser"  # custom browser binary (default: auto-detect Chrome)
config.BROWSER_RESTART_AFTER_BANS = 5  # restart Chrome (fresh fingerprint) after 5 consecutive bans
config.BROWSER_STATIC_ASSETS_BLOCK = True  # block images/fonts/CSS/media (skipped when snapshot=True)
config.BROWSER_PROXY_BYPASS_LIST = ["example.com", "*.internal"]  # these bypass the proxy


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
config.get("DEFAULT_ENGINE")  # "scrapy"
config.get("MISSING_KEY", "default")  # "default"
```

| Attribute                     | Type             | Default                           | Description                                                                                                                                                                                                                                                                                       |
|-------------------------------|------------------|-----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `DEFAULT_ENGINE`              | `str`            | `"scrapy"`                        | Engine used when `request.meta["stealth"]` key is absent                                                                                                                                                                                                                                          |
| `DEFAULT_PROFILE`             | `str`            | `"chrome_147"`                    | Browser profile used when none is specified                                                                                                                                                                                                                                                       |
| `DEFAULT_TIMEOUT`             | `int`            | `30`                              | Request timeout in seconds                                                                                                                                                                                                                                                                        |
| `STEALTH_DRIVER`              | `str`            | `"basic"`                         | Default driver: `"basic"`, `"turbo"`, or `"browser"`. Also readable from Scrapy settings as `STEALTH_DRIVER`                                                                                                                                                                                      |
| `HTTP2`                       | `bool`           | `True`                            | HTTP/2 mode; overridable per-request via `meta["stealth"]["http2"]`                                                                                                                                                                                                                               |
| `BLOCK_CODES`                 | `frozenset[int]` | `{403, 429, 503}`                 | HTTP status codes considered blocked                                                                                                                                                                                                                                                              |
| `BLOCK_KEYWORDS`              | `list[str]`      | `["captcha", "access denied", …]` | Body-text patterns considered blocked                                                                                                                                                                                                                                                             |
| `BROWSER_HEADLESS`            | `bool`           | `True`                            | Browser driver: headless mode (`False` = visible window, more stealthy)                                                                                                                                                                                                                           |
| `BROWSER_SETTLE_S`            | `float`          | `4.0`                             | Browser driver: seconds to wait after navigation for JS to finish rendering                                                                                                                                                                                                                       |
| `BROWSER_NO_SANDBOX`          | `bool \| None`   | `None`                            | Browser driver: disable Chrome sandbox. `None` = auto-detect (enabled when running as root, e.g. Docker)                                                                                                                                                                                          |
| `BROWSER_EXECUTABLE_PATH`     | `str \| None`    | `None`                            | Browser driver: path to the browser binary. `None` = auto-detect Chrome/Chromium. Set to use Brave or a custom install (e.g. `"/usr/bin/brave-browser"`)                                                                                                                                          |
| `BROWSER_MAX_TABS`            | `int`            | `10`                              | Browser driver: max concurrent Chrome tabs across in-flight requests                                                                                                                                                                                                                              |
| `BROWSER_RESTART_AFTER_BANS`  | `int`            | `5`                               | Browser driver: restart Chrome (fresh fingerprint/cookies/CDP session) after this many *consecutive* banned/challenged responses. Any clean response resets the count                                                                                                                             |
| `BROWSER_STATIC_ASSETS_BLOCK` | `bool`           | `False`                           | Browser driver: block images, fonts, CSS, and media via CDP. Overridable per-request via `meta["stealth"]["static_assets_block"]`; always off when `snapshot=True`                                                                                                                                |
| `BROWSER_PROXY_BYPASS_LIST`   | `list[str]`      | `[]`                              | Browser driver: domains/patterns that bypass the proxy and connect to the origin directly, via Chrome's `--proxy-bypass-list`. Supports wildcards (`*.example.com`), IP/CIDR, ports, and `<local>`. Only applies when a proxy is in use; set at browser launch (config/settings, not per-request) |

For one-off overrides on a single request, set `meta["stealth"]["driver"]` or `meta["stealth"]["http2"]` (see Per-Request Configuration
below).

---

## ⚙️ Per-Request Configuration

All options are passed via `request.meta["stealth"]`.

The presence of `meta["stealth"]` (a dict) activates the stealth engine. Omit the key to use the default Scrapy engine.
When `STEALTH_ENABLED = True`, all requests are stealth by default — pass `meta={"stealth": False}` to opt out for a specific request.

```python
yield scrapy.Request(
    url,
    meta={
        "stealth": {
            "driver": "turbo",
            "profile": "chrome_147",
            "proxy": "http://user:pass@proxy:8080",
            "stealth_timeout": 60,
            "http2": True,
            "rotate_proxy": True,
            "rotate_profile": True,
        }
    },
)
```

| Key                   | Type    | Description                                                                                                                                                                        |
|-----------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `driver`              | `str`   | `"basic"`, `"turbo"`, or `"browser"` — overrides `config.STEALTH_DRIVER` per-request                                                                                               |
| `profile`             | `str`   | Browser profile (e.g. `"chrome_147"`, `"safari_ios_18_1_1"`)                                                                                                                       |
| `proxy`               | `str`   | Explicit proxy URL                                                                                                                                                                 |
| `stealth_timeout`     | `int`   | Per-request timeout in seconds (overrides default 30s)                                                                                                                             |
| `http2`               | `bool`  | `True` = HTTP/2, `False` = HTTP/1.1 (overrides `config.HTTP2` for this request)                                                                                                    |
| `rotate_proxy`        | `bool`  | Auto-pick a proxy from `STEALTH_PROXIES`                                                                                                                                           |
| `rotate_profile`      | `bool`  | Auto-pick a random browser profile                                                                                                                                                 |
| `headless`            | `bool`  | Browser driver only: `True` = headless, `False` = visible window (more stealthy)                                                                                                   |
| `settle`              | `float` | Browser driver only: seconds to wait for JS after navigation (default `4.0`)                                                                                                       |
| `snapshot`            | `bool`  | Browser driver only: capture a PNG snapshot — result available as `response.meta["snapshot_content"]` (`bytes`)                                                                    |
| `static_assets_block` | `bool`  | Browser driver only: block images, fonts, CSS, and media for this request (overrides `config.BROWSER_STATIC_ASSETS_BLOCK`). Ignored — always unblocked — when `snapshot` is `True` |

---

## 🖥️ Browser Engine

For sites protected by Cloudflare JS challenges or heavy JavaScript rendering, use the `browser` driver.
It runs a real Chrome instance via the DevTools Protocol (no WebDriver), keeping one persistent browser
and opening a new tab per request.

**Per-request (most common):**

```python
yield scrapy.Request(
    url,
    meta={
        "stealth": {
            "driver": "browser",
            "headless": False,  # visible window — harder to detect (default: True)
            "settle": 4.0,  # seconds to wait for JS after page load
        }
    },
)
```

**Heavy Cloudflare sites — increase settle time:**

```python
meta = {"stealth": {"driver": "browser", "headless": False, "settle": 12}}
```

**Global default (all stealth requests use browser engine):**

```python
from scrapy_stealth.config import config

config.STEALTH_DRIVER = "browser"
config.BROWSER_HEADLESS = False  # more stealthy
config.BROWSER_SETTLE_S = 6.0  # longer wait for JS
```

**Custom browser binary (Brave, Chromium, or a non-default Chrome install):**

```python
from scrapy_stealth.config import config

config.BROWSER_EXECUTABLE_PATH = "/usr/bin/brave-browser"  # Linux
# config.BROWSER_EXECUTABLE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"  # Windows
```

Or via `settings.py` / `custom_settings`:

```python
BROWSER_EXECUTABLE_PATH = "/usr/bin/brave-browser"
```

> When `BROWSER_EXECUTABLE_PATH` is `None` (the default), `scrapy-stealth` auto-detects Google Chrome or Chromium from standard system
> paths. Set it explicitly when using Brave or a non-standard Chrome installation — a clear error is raised if the path does not exist.

**Intelligent restart:**

The browser engine restarts Chrome intelligently rather than on a fixed schedule — it only restarts
(getting a fresh fingerprint, cookies, and CDP session) after `BROWSER_RESTART_AFTER_BANS` consecutive
banned/challenged responses, as classified by the Anti-Bot Detection module (see below).
A single clean response resets the streak, so a browser that's sailing through cleanly is left running
indefinitely — it's never restarted just because it has served a lot of requests.

```python
from scrapy_stealth.config import config

config.BROWSER_RESTART_AFTER_BANS = 5  # restart after 5 consecutive bans (default)
```

**Static asset blocking:**

scrapy-stealth can block static assets (images, fonts, CSS, and media) in the browser to speed up
page loads and cut bandwidth, via the CDP Fetch domain. It's off by default — enable it globally with
`BROWSER_STATIC_ASSETS_BLOCK = True` in `settings.py`, or per-request via
`meta["stealth"]["static_assets_block"]`. Blocking is always skipped when `snapshot=True`, since a
snapshot needs the fully rendered page.

```python
# settings.py
BROWSER_STATIC_ASSETS_BLOCK = True
```

```python
# per-request
meta = {"stealth": {"driver": "browser", "static_assets_block": True}}
```

```python
# snapshot always wins — assets are never blocked here, even with the global default on
meta = {"stealth": {"driver": "browser", "snapshot": True}}
```

**Proxy bypass list:**

When a proxy is configured, you can send specific domains straight to the origin instead of
through the proxy. The list is passed to Chrome's `--proxy-bypass-list` launch flag, so it
supports the full Chrome bypass syntax — bare hostnames, wildcards (`*.example.com`),
IP/CIDR ranges, ports, and the special `<local>` token.

```python
# settings.py
STEALTH_DRIVER = "browser"
STEALTH_PROXIES = ["http://user:pass@proxy:8080"]
BROWSER_PROXY_BYPASS_LIST = [
    "example.com",  # exact host
    "*.internal.net",  # wildcard subdomains
    "127.0.0.1",  # IP
    "<local>",  # any plain hostname without dots
]
```

```python
# or via config
from scrapy_stealth.config import config

config.BROWSER_PROXY_BYPASS_LIST = ["example.com", "*.internal.net"]
```

> The bypass list is a Chrome launch flag, so it's read once when the browser starts and
> applies to the whole browser lifetime — it's configured globally (config/settings), not
> per-request. It has no effect unless a proxy is in use.

**Docker (running as root):**

Chrome requires `--no-sandbox` when the process runs as root. `scrapy-stealth` detects this automatically,
but you can also set it explicitly in `settings.py`:

```python
BROWSER_NO_SANDBOX = True  # force no-sandbox (Docker, any root environment)
BROWSER_EXECUTABLE_PATH = "/usr/bin/chromium"  # use Chromium instead of Chrome in Docker
```

Or via `config`:

```python
config.BROWSER_NO_SANDBOX = True
config.BROWSER_EXECUTABLE_PATH = "/usr/bin/chromium"
```

> **Performance note**: the browser engine is slower than `basic`/`turbo` (~5-15s per page vs <2s).
> Use it selectively — route only JS-protected URLs to `"browser"` and keep everything else on `"turbo"`.

---

## 📸 Screenshots

Capture a PNG screenshot of any page rendered by the `browser` driver and save it to disk.

### Enable on the request

```python
yield scrapy.Request(
    url,
    meta={
        "stealth": {
            "driver": "browser",
            "snapshot": True,
        }
    },
    callback=self.parse,
)
```

The raw PNG bytes are available at `response.meta["snapshot_content"]` inside your callback.

### Auto-save with `snapshot` decorator

```python
from scrapy_stealth.decorators import snapshot


class MySpider(scrapy.Spider):

    @snapshot
    def parse(self, response): ...

    @snapshot(path="stealth_shots/page.png")
    def parse(self, response): ...

    @snapshot(path=lambda r: r.url.split("/")[-1] + ".png")
    def parse(self, response): ...
```

> **Note:** Requires `driver="browser"` and `snapshot=True` in the request meta.
> Logs an error if no snapshot data is found in the response.

### Custom handling (without the built-in helper)

The screenshot is just `bytes` in `response.meta["snapshot_content"]` — do anything you like with it:

```python
def parse(self, response):
    shot: bytes | None = response.meta.get("snapshot_content")
    if shot is None:
        return  # screenshot was not requested or capture failed

    # Save manually
    with open("page.png", "wb") as f:
        f.write(shot)

    # Pass to a pipeline via item
    yield {"url": response.url, "screenshot": shot}
```

---

## 🔁 Automatic Rotation

```python
yield scrapy.Request(
    url,
    meta={
        "stealth": {
            "rotate_proxy": True,
            "rotate_profile": True,
        }
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
        "stealth": {
            "proxy": proxy_rotator.get(),
        }
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
        "stealth": {
            "profile": fp.get(),
        }
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
                "stealth": {
                    "rotate_proxy": True,
                    "rotate_profile": True,
                }
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

See [CHANGELOG.md](https://github.com/fawadss1/scrapy-stealth/blob/master/CHANGELOG.md) for a full history of changes, or
browse [GitHub Releases](https://github.com/fawadss1/scrapy-stealth/releases).

---

## 🤝 Contributing

See [CONTRIBUTING.md](https://github.com/fawadss1/scrapy-stealth/blob/master/CONTRIBUTING.md) for guidelines on how to contribute.

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute.
See [LICENSE](https://github.com/fawadss1/scrapy-stealth/blob/master/LICENSE) for the full text.