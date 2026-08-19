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

## 💜 Sponsors

<table>
  <tr>
    <td colspan="2" align="center">
      <a href="https://go.nodemaven.com/Fawadss1readmegh">
        <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/sponsors/nodemaven-banner.png" alt="NodeMaven — Best proxy for web scrapping and automation with the highest quality IP" width="720"/>
      </a>
    </td>
  </tr>
  <tr>
    <td colspan="2">
      <strong><a href="https://go.nodemaven.com/Fawadss1readmegh">NodeMaven</a></strong> — the most efficient proxy provider for web scrapping and automation with the highest-quality IP on the market.
      <br/><br/>
      <strong>Why <a href="https://go.nodemaven.com/Fawadss1readmegh">NodeMaven</a>?</strong>
      <ul>
        <li>99.9% uptime</li>
        <li>ZIP Targeting</li>
        <li>IP filtering: all proxies have fraud score &lt;97%</li>
        <li>No KYC required</li>
        <li>Unique free tools: <a href="https://go.nodemaven.com/Fawadss1tools">Proxy Bandwidth Checker</a>, Meta Tag Checker, IP Lookup, and others</li>
      </ul>
      Special codes for scrapy-stealth users:
      <code>SCRAPYSTEALTH35</code> — 35% off Mobile and Residential Proxies;
      <code>SCRAPYSTEALTH40</code> — 40% off ISP (Static) Proxies.
    </td>
  </tr>
  <tr>
    <td width="160" align="center">
      <a href="https://proxy-seller.com/?utm_source=github&utm_medium=referral&utm_campaign=partner_promo&utm_term=github&partner=C2796BDED58F4875">
        <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/sponsors/proxy-seller-logo.png" alt="Proxy-Seller" width="120"/>
      </a>
    </td>
    <td>
      <strong><a href="https://proxy-seller.com/?utm_source=github&utm_medium=referral&utm_campaign=partner_promo&utm_term=github&partner=C2796BDED58F4875">Proxy-Seller</a></strong> — residential, ISP, mobile, IPv4, and IPv6 proxies across 220+ locations. HTTP(S) and SOCKS5, flexible rotation, and 24/7 support — built for scraping, SEO, and automation at scale.
      <br/><br/>
      Use code <code>FAWAD15</code> at <a href="https://proxy-seller.com/?utm_source=github&utm_medium=referral&utm_campaign=partner_promo&utm_term=github&partner=C2796BDED58F4875">proxy-seller.com</a>.
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
| TLS fingerprint spoofing     |       ✅       |         ✅         |        ❌         |      ❌       |        ❌        |
| HTTP/2 support               |       ✅       |         ✅         |        ✅         |      ❌       |        ❌        |
| Browser impersonation        |       ✅       |         ✅         |    ⚠️ partial     |      ❌       |        ❌        |
| Proxy rotation (built-in)    |       ✅       |         ❌         |        ❌         |      ❌       |        ❌        |
| Fingerprint rotation         |       ✅       |         ❌         |        ❌         |      ❌       |        ❌        |
| Anti-bot detection           |       ✅       |         ❌         |        ❌         |      ❌       |        ❌        |
| Smart browser selection      |       ✅       |         ❌         |        ❌         |      ❌       |        ❌        |
| Smart retry logic            |       ✅       |         ❌         |        ❌         |      ❌       |        ❌        |
| Per-request engine switching |       ✅       |         ❌         |        ❌         |      ❌       |        ❌        |
| Headless browser required    |       ✅       |         ❌         |        ✅         |      ✅       |        ❌        |
| JavaScript rendering         |       ️✅       |         ❌         |        ✅         |      ✅       |        ❌        |
| Screenshot / snapshot        |       ✅       |         ❌         |        ✅         |      ✅       |        ❌        |
| Native Scrapy integration    |       ✅       |         ✅         |        ✅         |      ✅       |        ✅        |
| Memory footprint             |     🟢 Low     |       🟢 Low       |      🔴 High      |    🔴 High    |      🟢 Low      |

> ⚠️ `scrapy-playwright` passes real browser TLS but does not spoof fingerprint profiles like `scrapy-stealth` does.
> `scrapy-impersonate` provides TLS/HTTP2 impersonation but lacks built-in rotation, detection, or per-request engine
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
* 🧠 **Smart browser selection** — `driver="auto"` runs fast `basic` / `turbo` first, then retries once with visible Chrome on JS challenge or ban (enabled automatically when `STEALTH_ENABLED = True`)
* ⚡ Thread-safe async integration
* 🖥️ Real-browser engine (CDP) for JS-heavy pages
* 🔄 Intelligent session recycle — after consecutive bans, browser restarts Chrome; basic/turbo clear HTTP sessions
* 🚫 Static asset blocking — skip images, fonts, CSS, and media for faster, lighter browser fetches
* 🎯 Proxy bypass list — send chosen domains straight to the origin instead of through the proxy (`--proxy-bypass-list`)
* 🧭 Custom DNS overrides — pin hosts to fixed IPs (connect via IP, keep hostname for TLS/SNI/Host) to dodge poisoned or geo-shifted public DNS
* 📤 **Full request fidelity** — `POST`/`PUT`/`PATCH`/`DELETE`, custom headers, and `Cookie` work the same on `basic`, `turbo`, and `browser`
* 🍪 **Browser cookie handoff** — after browser login/navigation, session cookies export to response meta and merge into Scrapy's cookie jar for follow-up `basic`/`turbo` requests
* ☁️ **Cloudflare challenge handling** — browser driver waits through 403/503 interstitials and Turnstile-style pages (up to `BROWSER_CHALLENGE_TIMEOUT_S`); returns raw bytes for CDN images (`.jpg`, `.png`, …) instead of Chrome’s HTML viewer shell
* 📸 Built-in snapshot decorator (`scrapy_stealth.decorators.snapshot`)

---

## 📦 Installation

```bash
pip install scrapy-stealth
```

> Requires Python 3.11+ and Scrapy 2.12–2.x

---

## ⚙️ Setup

**Recommended — two settings, smart by default:**

```python
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
}
STEALTH_ENABLED = True  # injects driver="auto" on every request
```

That runs fast HTTP impersonation with **`turbo`** first (deeper TLS fingerprinting), then retries once with visible Chrome when a JS challenge or session ban is detected. No extra fallback flags — `driver="auto"` is the only switch.

### Option 1 — Global (`settings.py`)

```python
# 1. Enable the middleware
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
}

# 2. Route ALL requests through stealth — injects driver="auto" automatically (turbo first)
STEALTH_ENABLED = True
# STEALTH_DRIVER = "basic"  # optional: lighter HTTP driver instead of default turbo

# 3. (Optional) Proxy list — seeded as engine default; rotated on ban-streak session recycle
#    Supported schemes: http, https, socks4, socks5
STEALTH_PROXIES = [
    "http://proxy1:8080",
    "http://proxy2:8080",
    "http://user:pass@proxy3:8080",  # with authentication
    "socks5://proxy4:1080",
]

# 4. (Optional) Pin hosts to fixed origin IPs (bypass public DNS)
#    Connects to the IP while keeping the hostname for TLS SNI / Host / certs
STEALTH_DNS_OVERRIDES = {
    "example.com": "203.0.113.10",
    "www.example.com": "203.0.113.10",
}
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
        "STEALTH_PROXIES": [
            "http://proxy1:8080",
            "http://user:pass@proxy2:8080",
            "socks5://proxy3:1080",
        ],
        "STEALTH_DNS_OVERRIDES": {
            "example.com": "203.0.113.10",
        },
    }
```

> Proxies are validated at startup — invalid format or unsupported scheme raises `ValueError` immediately.
> DNS overrides are validated the same way — invalid IPs raise `ValueError` immediately.

---

## 🚀 Quick Start

**Option A — Per-request** (stealth on specific URLs only):

```python
# Smart path — HTTP first, browser on challenge/ban
yield scrapy.Request(
    url="https://example.com",
    meta={"stealth": {"driver": "auto"}},
)

# HTTP-only — no browser fallback
yield scrapy.Request(
    url="https://example.com",
    meta={"stealth": {"driver": "basic"}},
)
```

**Option B — Global mode** (recommended — stealth on every request):

```python
# settings.py or custom_settings
STEALTH_ENABLED = True
# STEALTH_DRIVER = "basic"  # optional: lighter HTTP driver instead of default turbo
```

```python
# No meta needed — middleware injects driver="auto"
yield scrapy.Request(url="https://example.com")

# Opt out for a specific request
yield scrapy.Request(url="https://api.internal/health", meta={"stealth": False})

# Force HTTP-only for one request (no browser fallback)
yield scrapy.Request(url="https://example.com", meta={"stealth": {"driver": "basic"}})
```

See [Smart browser selection](#-smart-browser-selection) for how `driver="auto"` works.

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
config.STEALTH_DRIVER = "turbo"  # "turbo" (default), "basic", "browser", or "auto"
config.HTTP2 = True  # False for servers that only support HTTP/1.1
config.BLOCK_CODES |= {407}  # extend blocked status codes (|= keeps defaults)
config.BLOCK_KEYWORDS.append("banned")  # extend blocked body-text patterns
config.BROWSER_HEADLESS = False  # browser driver: False = visible window (default)
config.BROWSER_SETTLE_S = 4.0  # browser driver: seconds to wait after navigation for JS to finish
config.BROWSER_CHALLENGE_TIMEOUT_S = 30.0  # max wait on Cloudflare / JS challenge pages (403/503)
config.BROWSER_EXECUTABLE_PATH = "/usr/bin/brave-browser"  # custom browser binary (default: auto-detect Chrome)
config.STEALTH_RECYCLE_AFTER_BANS = 5  # recycle Chrome / HTTP sessions after 5 consecutive bans
config.BROWSER_STATIC_ASSETS_BLOCK = True  # block images/fonts/CSS/media (skipped when snapshot=True)
config.BROWSER_PROXY_BYPASS_LIST = ["example.com", "*.internal"]  # these bypass the proxy
config.STEALTH_DNS_OVERRIDES = {"example.com": "203.0.113.10"}  # pin host → origin IP


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

| Attribute                     | Type             | Default                           | Description                                                                                                                                                                                                                                                                                               |
|-------------------------------|------------------|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `DEFAULT_ENGINE`              | `str`            | `"scrapy"`                        | Engine used when `request.meta["stealth"]` key is absent                                                                                                                                                                                                                                                  |
| `DEFAULT_PROFILE`             | `str`            | `"chrome_147"`                    | Browser profile used when none is specified                                                                                                                                                                                                                                                               |
| `DEFAULT_TIMEOUT`             | `int`            | `30`                              | Request timeout in seconds                                                                                                                                                                                                                                                                                |
| `STEALTH_DRIVER`              | `str`            | `"turbo"`                         | Primary HTTP driver when `driver="auto"`. Also the default when no driver is set on a per-request stealth dict. Options: `"basic"`, `"turbo"`, `"browser"`, `"auto"`. Readable from Scrapy settings as `STEALTH_DRIVER`                                                                                   |
| `STEALTH_ENABLED`             | `bool`           | `False`                           | When `True`, route every request through stealth and inject `driver="auto"` unless the request already sets a driver or opts out with `meta={"stealth": False}`                                                                                                                                           |
| `HTTP2`                       | `bool`           | `True`                            | HTTP/2 mode; overridable per-request via `meta["stealth"]["http2"]`                                                                                                                                                                                                                                       |
| `BLOCK_CODES`                 | `frozenset[int]` | `{403, 429, 503}`                 | HTTP status codes considered blocked                                                                                                                                                                                                                                                                      |
| `BLOCK_KEYWORDS`              | `list[str]`      | `["captcha", "access denied", …]` | Body-text patterns considered blocked                                                                                                                                                                                                                                                                     |
| `BROWSER_HEADLESS`            | `bool`           | `False`                           | Browser driver: headless mode (`False` = visible window, default and more stealthy)                                                                                                                                                                                                                       |
| `BROWSER_SETTLE_S`            | `float`          | `4.0`                             | Browser driver: seconds to wait after navigation for JS to finish rendering                                                                                                                                                                                                                               |
| `BROWSER_CHALLENGE_TIMEOUT_S` | `float`          | `30.0`                            | Browser driver: max seconds to wait on JS challenge / Cloudflare interstitial pages (403/503, “Just a moment”, Turnstile). Uses `challenge_mode` polling — longer than `BROWSER_SETTLE_S`                                                                                                                 |
| `BROWSER_NO_SANDBOX`          | `bool \| None`   | `None`                            | Browser driver: disable Chrome sandbox. `None` = auto-detect (enabled when running as root, e.g. Docker)                                                                                                                                                                                                  |
| `BROWSER_EXECUTABLE_PATH`     | `str \| None`    | `None`                            | Browser driver: path to the browser binary. `None` = auto-detect Chrome/Chromium. Set to use Brave or a custom install (e.g. `"/usr/bin/brave-browser"`)                                                                                                                                                  |
| `BROWSER_MAX_TABS`            | `int`            | `10`                              | Browser driver: max concurrent Chrome tabs across in-flight requests                                                                                                                                                                                                                                      |
| `STEALTH_RECYCLE_AFTER_BANS`  | `int`            | `5`                               | After this many *consecutive* bans: `browser` restarts Chrome; `basic` / `turbo` clear cached HTTP sessions/clients. Any clean response resets the count                                                                                                                                                  |
| `BROWSER_STATIC_ASSETS_BLOCK` | `bool`           | `False`                           | Browser driver: block images, fonts, CSS, and media via CDP. Overridable per-request via `meta["stealth"]["static_assets_block"]`; always off when `snapshot=True`                                                                                                                                        |
| `BROWSER_EXPORT_COOKIES`      | `bool`           | `True`                            | After each browser response, merge tab cookies into Scrapy's cookie jar when `COOKIES_ENABLED` is on. Per-request opt-out: `meta["stealth"]["export_cookies"] = False`. Cookies are always exposed on the response either way (see [Browser cookie handoff](#browser-cookie-handoff))                     |
| `BROWSER_PROXY_BYPASS_LIST`   | `list[str]`      | `[]`                              | Browser driver: domains/patterns that bypass the proxy and connect to the origin directly, via Chrome's `--proxy-bypass-list`. Supports wildcards (`*.example.com`), IP/CIDR, ports, and `<local>`. Only applies when a proxy is in use; set at browser launch (config/settings, not per-request)         |
| `STEALTH_DNS_OVERRIDES`       | `dict[str, str]` | `{}`                              | Host→IP map used by `basic` / `turbo` (and Chrome `--host-resolver-rules` for `browser`). Connects to the IP while keeping the hostname for TLS SNI, Host header, and cert verification. Also readable from Scrapy settings as `STEALTH_DNS_OVERRIDES`. Per-request override via `meta["stealth"]["dns"]` |

For one-off overrides on a single request, set `meta["stealth"]["driver"]` or `meta["stealth"]["http2"]` (see Per-Request Configuration
below).

---

## ⚙️ Per-Request Configuration

All options are passed via `request.meta["stealth"]`.

The presence of `meta["stealth"]` (a dict) activates the stealth engine. Omit the key to use the default Scrapy engine.
When `STEALTH_ENABLED = True`, all requests are stealth by default with `driver="auto"` — pass `meta={"stealth": False}` to opt out, or set an explicit `driver` to override.

```python
yield scrapy.Request(
    url,
    meta={
        "stealth": {
            "driver": "turbo",
            # optional overrides — otherwise profile/proxy come from defaults and
            # rotate automatically when the session recycles after consecutive bans
            "profile": "chrome_147",
            "proxy": "http://user:pass@proxy:8080",
            "stealth_timeout": 60,
            "http2": True,
            "dns": "203.0.113.10",  # or {"example.com": "203.0.113.10"}
        }
    },
)
```

| Key                   | Type            | Description                                                                                                                                                                                                                                                                 |
|-----------------------|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `driver`              | `str`           | `"basic"`, `"turbo"`, `"browser"`, or `"auto"`. Use `"auto"` for smart selection: HTTP first (`STEALTH_DRIVER`), then one browser retry on challenge/ban. Injected automatically when `STEALTH_ENABLED = True`. `"basic"` / `"turbo"` alone do **not** fall back to browser |
| `fallback`            | `bool`          | Set to `False` to disable the browser retry when `driver="auto"` is active                                                                                                                                                                                                  |
| `profile`             | `str`           | Browser profile (e.g. `"chrome_147"`, `"safari_ios_18_1_1"`). Omit to use engine default; default rotates on ban-streak session recycle                                                                                                                                     |
| `proxy`               | `str`           | Explicit proxy URL. Omit to use `STEALTH_PROXIES` default; default rotates on ban-streak session recycle                                                                                                                                                                    |
| `dns`                 | `str` or `dict` | Pin DNS: bare IP for this request's hostname, or `{host: ip}` mapping. Merges over `STEALTH_DNS_OVERRIDES`. Works with `basic`/`turbo` per-request; `browser` uses global overrides at Chrome launch only                                                                   |
| `stealth_timeout`     | `int`           | Per-request timeout in seconds (overrides default 30s)                                                                                                                                                                                                                      |
| `http2`               | `bool`          | `True` = HTTP/2, `False` = HTTP/1.1 (overrides `config.HTTP2` for this request)                                                                                                                                                                                             |
| `headless`            | `bool`          | Browser driver only: `False` = visible window (default), `True` = headless                                                                                                                                                                                                  |
| `settle`              | `float`         | Browser driver only: seconds to wait for JS after navigation (default `4.0`)                                                                                                                                                                                                |
| `snapshot`            | `bool`          | Browser driver only: capture a PNG snapshot — result available as `response.meta["snapshot_content"]` (`bytes`)                                                                                                                                                             |
| `static_assets_block` | `bool`          | Browser driver only: block images, fonts, CSS, and media for this request (overrides `config.BROWSER_STATIC_ASSETS_BLOCK`). Ignored — always unblocked — when `snapshot` is `True`                                                                                          |
| `export_cookies`      | `bool`          | Browser driver only: merge tab cookies into Scrapy's cookie jar on the response (default follows `BROWSER_EXPORT_COOKIES`). Set `False` to skip jar merge while still receiving `browser_cookies` / `browser_cookie_header` on the response                                 |

**Response meta (browser driver):** after each browser fetch, the response includes:

| Key                                                 | Type         | Description                                                                |
|-----------------------------------------------------|--------------|----------------------------------------------------------------------------|
| `response.meta["stealth"]["browser_cookies"]`       | `list[dict]` | Cookies read from the tab (name, value, domain, path, secure, httpOnly, …) |
| `response.meta["stealth"]["browser_cookie_header"]` | `str`        | Ready-to-use `Cookie` request header string                                |

---

## 📤 POST, headers, and cookies

All stealth drivers (`basic`, `turbo`, `browser`, and `driver="auto"`) honor the **same Scrapy
`Request` fields** — HTTP method, body, `Cookie`, and custom headers. Use normal Scrapy syntax;
no extra stealth meta keys are required for POST or auth headers.

Internally, every driver calls `build_stealth_request()` to normalize and validate the request
once (method, URL, body, cookies, headers). Fingerprint headers (`User-Agent`, `Accept`,
`sec-ch-ua`, etc.) are managed by the engine impersonation layer — set `Authorization`,
`Content-Type`, `Cookie`, and other app-specific headers on the Scrapy request as usual.

### JSON POST (API login, search, etc.)

Works on **`basic`**, **`turbo`**, and **`browser`**.  
Use [`postman-echo.com/post`](https://postman-echo.com/post) — it echoes JSON back and stays up
reliably (avoid `httpbin.org`; it often returns **503**):

```python
import json

yield scrapy.Request(
    "https://postman-echo.com/post",
    method="POST",
    body=json.dumps({"search": "laptop", "page": 1}).encode(),
    headers={"Content-Type": "application/json"},
    meta={"stealth": {"driver": "turbo"}},  # or basic / browser / auto
)
```

With global stealth enabled, omit `meta` — the same request shape applies:

```python
STEALTH_ENABLED = True  # settings.py

yield scrapy.Request(
    "https://postman-echo.com/post",
    method="POST",
    body=json.dumps({"search": "laptop"}).encode(),
    headers={"Content-Type": "application/json"},
)
```

> **Connection failed on turbo?** If you use `STEALTH_PROXIES` or `meta["stealth"]["proxy"]`,
> the proxy must allow HTTPS POST to the test host. Try without a proxy first, or switch to
> `driver="basic"`, or set `meta={"stealth": {"http2": False}}`.

### Form POST (login, filters)

[`quotes.toscrape.com/login`](https://quotes.toscrape.com/login) is a public Scrapy tutorial site with a real login form:

```python
from urllib.parse import urlencode

yield scrapy.Request(
    "https://quotes.toscrape.com/login",
    method="POST",
    body=urlencode({"username": "admin", "password": "admin"}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    meta={"stealth": {"driver": "browser"}},  # browser merges hidden csrf_token from the form
)
```

> **Browser form POST:** the engine loads the login page first, then merges hidden `<form>` fields (e.g. `csrf_token`) into urlencoded bodies before in-page `fetch()`. You only need to send the visible fields (`username`, `password`, …).

### Browser cookie handoff

After a browser request (login POST, JS navigation, etc.), scrapy-stealth reads cookies from the Chrome tab and exposes them on the response. When `COOKIES_ENABLED = True` (Scrapy default) and `BROWSER_EXPORT_COOKIES = True` (default), those cookies are merged into Scrapy's cookie jar so the next `basic` or `turbo` request reuses the session automatically.

**Typical flow: login with browser → scrape with turbo**

```python
from urllib.parse import urlencode

class LoginSpider(scrapy.Spider):
    custom_settings = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
        },
        "COOKIES_ENABLED": True,
    }

    async def start(self):
        yield scrapy.Request(
            "https://quotes.toscrape.com/login",
            method="POST",
            body=urlencode({"username": "admin", "password": "admin"}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            meta={"stealth": {"driver": "browser"}},
            callback=self.after_login,
        )

    def after_login(self, response):
        # Optional: inspect exported cookies
        stealth = response.meta.get("stealth") or {}
        self.logger.info("cookie header: %s", stealth.get("browser_cookie_header"))

        # Jar merge is automatic — turbo/basic pick up the session
        yield scrapy.Request(
            "https://quotes.toscrape.com/",
            meta={"stealth": {"driver": "turbo"}},
            callback=self.parse_home,
        )

    def parse_home(self, response):
        assert "Logout" in response.text  # still logged in via turbo
```

Or pass cookies explicitly on the next request:

```python
cookie_header = response.meta["stealth"]["browser_cookie_header"]
yield scrapy.Request(
    url,
    headers={"Cookie": cookie_header},
    meta={"stealth": {"driver": "turbo"}},
)
```

Opt out of jar merge per request (meta is still populated):

```python
meta={"stealth": {"driver": "browser", "export_cookies": False}}
```

Stats: `stealth/browser_cookies_exported` counts cookies merged into the jar.

### Cookies and Authorization

Pass session cookies or bearer tokens on the Scrapy request — all drivers forward them.  
[`postman-echo.com/get`](https://postman-echo.com/get) echoes request headers back:

```python
yield scrapy.Request(
    "https://postman-echo.com/get",
    headers={
        "Cookie": "session_id=abc123; cart_token=xyz",
        "Authorization": "Bearer test-token-123",
    },
    meta={"stealth": {"driver": "turbo"}},
)
```

> **Tip:** With `COOKIES_ENABLED = True`, browser-exported session cookies flow into Scrapy's jar automatically (`BROWSER_EXPORT_COOKIES = True` by default). You can also set the `Cookie` header manually on any driver — all engines forward it.

### PUT / PATCH / DELETE

Same pattern — set `method` and optional `body`.  
[`jsonplaceholder.typicode.com/posts/1`](https://jsonplaceholder.typicode.com/posts/1) accepts PATCH:

```python
yield scrapy.Request(
    "https://jsonplaceholder.typicode.com/posts/1",
    method="PATCH",
    body=b'{"title": "patched"}',
    headers={"Content-Type": "application/json"},
    meta={"stealth": {"driver": "basic"}},
)
```

### Driver behaviour summary

| Driver    | GET / HEAD                                                              | POST / PUT / PATCH / DELETE / …      |
|-----------|-------------------------------------------------------------------------|--------------------------------------|
| `basic`   | Native HTTP client + profile TLS                                        | Same — method + body + headers       |
| `turbo`   | curl-impersonate TLS fingerprint                                        | Same — method + body + headers       |
| `browser` | Chrome tab navigation; binary URLs (`.jpg`, `.png`, …) return raw bytes | In-page `fetch()` with method + body |

For **`driver="auto"`**, phase 1 uses `basic`/`turbo` (including POST). If the response is a
JS challenge or session ban, phase 2 retries once with **`browser`** using the same method,
body, and headers. Fallback counters include the HTTP method (`stealth/fallbacks/method/post`,
etc.).

### What not to set manually

Do **not** override fingerprint headers on the Scrapy request — they are stripped and replaced
by the active profile:

* `User-Agent`, `Accept`, `Accept-Language`, `Accept-Encoding`
* `sec-ch-ua*`, `sec-fetch-*`, `Upgrade-Insecure-Requests`, etc.

Set application headers only (`Content-Type`, `Cookie`, `Authorization`, `X-*`, …).

### JS-protected POST flows

When a site requires a real browser for login or API calls behind Cloudflare, point at a live
endpoint — here [`postman-echo.com/post`](https://postman-echo.com/post) via the browser driver
(swap in your target URL for production):

```python
yield scrapy.Request(
    "https://postman-echo.com/post",
    method="POST",
    body=b'{"items": [{"sku": "A1", "qty": 2}]}',
    headers={"Content-Type": "application/json"},
    meta={"stealth": {"driver": "browser", "headless": False, "settle": 6}},
)
```

For a JS-rendered **GET** smoke test, try [`quotes.toscrape.com`](https://quotes.toscrape.com/)
with `driver="browser"`.

Or let `driver="auto"` try fast HTTP first and escalate to browser only when needed.

---

## 🧭 Custom DNS Overrides

Pin a hostname to a fixed origin IP so the package dials that address directly instead of trusting public DNS.
The request URL stays as `https://example.com/...` — TLS SNI, the `Host` header, and certificate verification still use the hostname.

**Global (`settings.py` / `custom_settings` / `config`):**

```python
STEALTH_DNS_OVERRIDES = {
    "shop.example.com": "203.0.113.10",
    "cdn.example.com": "203.0.113.11",
}
```

**Per-request** (overrides or extends the global map):

```python
yield scrapy.Request(
    "https://shop.example.com/item/1",
    meta={"stealth": {"driver": "turbo", "dns": "203.0.113.10"}},
)

# Or a full mapping:
meta = {"stealth": {"dns": {"shop.example.com": "203.0.113.10"}}}
```

Supported on `basic` and `turbo` per-request. The `browser` driver applies the effective map
(config + `meta["stealth"]["dns"]`) via a **local CONNECT relay** that dials the pinned IP
(Chrome's `--host-resolver-rules` is not used — it is unreliable). Chrome is pointed at the
relay with `--proxy-server`; when the DNS map changes, the browser restarts so the relay is
rebuilt. Do not put DNS-pinned hosts on `BROWSER_PROXY_BYPASS_LIST` or they will skip the relay.
With an HTTP proxy on `basic`/`turbo`, DNS is often resolved by the proxy — prefer direct
connections or SOCKS when using overrides.

## 🧠 Smart browser selection

Use `driver="auto"` to pick the right engine automatically: stay on fast HTTP impersonation (`basic` / `turbo`) for normal pages, and escalate to real Chrome only when the response looks like a JS challenge or session ban (403/429/503, Cloudflare “Just a moment”, Akamai, DataDome, and similar signals).

> **Note:** The removed `STEALTH_AUTO_FALLBACK` setting is no longer needed. Browser fallback is controlled solely by `driver="auto"`. When `STEALTH_ENABLED = True`, the middleware injects it for you.

| Phase | Driver                       | When                                                           |
|-------|------------------------------|----------------------------------------------------------------|
| 1     | `turbo` (default) or `basic` | First attempt — low memory, high throughput (`STEALTH_DRIVER`) |
| 2     | `browser` (`headless=False`) | One retry when phase 1 is blocked or challenged                |

The fallback always opens a **visible Chrome window** (`headless=False`) for better evasion —
regardless of `BROWSER_HEADLESS` or any prior `meta["stealth"]["headless"]` value.

**Global — simplest setup:**

```python
STEALTH_ENABLED = True
# STEALTH_DRIVER = "basic"  # optional — lighter HTTP driver instead of default turbo
```

**Per-request** (without `STEALTH_ENABLED`):

```python
yield scrapy.Request(
    url,
    meta={"stealth": {"driver": "auto"}},
)
```

**Always use browser** (skip phase 1):

```python
meta={"stealth": {"driver": "browser"}}
```

**HTTP-only** (no browser retry):

```python
meta={"stealth": {"driver": "basic"}}  # or "turbo"
```

**Disable browser retry but keep auto HTTP driver** (rare):

```python
meta={"stealth": {"driver": "auto", "fallback": False}}
```

Each request is retried at most once. If the browser fetch fails, the original `basic` / `turbo`
response is returned. Console output and stats (`stealth/fallbacks`, `stealth/fallbacks/method/post`,
`stealth/requests/browser`) show when escalation happened.

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
            "headless": False,  # visible window — default for browser driver
            "settle": 4.0,  # seconds to wait for JS after page load
        }
    },
)
```

**Heavy Cloudflare sites — increase settle and challenge timeout:**

```python
meta = {
    "stealth": {
        "driver": "browser",
        "headless": False,
        "settle": 12,
    }
}

# Or globally:
# BROWSER_CHALLENGE_TIMEOUT_S = 45
```

On 403/503 challenge pages (“Just a moment”, “Performing security verification”, Turnstile),
the browser driver waits up to `BROWSER_CHALLENGE_TIMEOUT_S` (default 30s) for the challenge
to clear before capturing the response — not only on HTTP 2xx.

**CDN images / binary assets behind Cloudflare:**

Direct GET to `.jpg`, `.png`, and other asset URLs returns **raw file bytes** in
`response.body` (not Chrome’s HTML image-viewer wrapper). Useful for CDN hosts like
`scdn.autodoc.de`:

```python
yield scrapy.Request(
    "https://scdn.autodoc.de/vehicles/800x287/8145.jpg",
    meta={"stealth": {"driver": "browser", "headless": False, "settle": 8}},
    callback=self.save_image,
)

def save_image(self, response):
    assert response.body[:3] == b"\xff\xd8\xff"  # JPEG magic bytes
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

**Intelligent restart / session recycle:**

After `STEALTH_RECYCLE_AFTER_BANS` consecutive banned/challenged responses (as classified by
Anti-Bot Detection), scrapy-stealth recycles the driver session:

* **browser** — restarts Chrome (fresh fingerprint, cookies, CDP session)
* **basic / turbo** — clears cached HTTP clients/sessions and rotates default fingerprint
  profile + proxy from `STEALTH_PROXIES` (no per-request `rotate_*` needed)

A single clean response resets the streak, so a healthy crawl is never recycled just because it
has served a lot of requests.

```python
from scrapy_stealth.config import config

config.STEALTH_RECYCLE_AFTER_BANS = 5  # recycle after 5 consecutive bans (default)
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
> With `driver="auto"` (or `STEALTH_ENABLED = True`), only challenged URLs hit the browser — everything else stays on fast HTTP.

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

Profile + proxy stay stable for speed (session reuse). After
`STEALTH_RECYCLE_AFTER_BANS` consecutive bans, the session recycles and a new
default profile + proxy (from `STEALTH_PROXIES`) are chosen automatically.

```python
# settings.py
STEALTH_PROXIES = ["http://proxy1:8080", "http://proxy2:8080"]
STEALTH_RECYCLE_AFTER_BANS = 5  # default

# spider — per-request stealth with explicit driver (no auto injection)
yield scrapy.Request(url, meta={"stealth": {"driver": "turbo"}})
```

**Scrapy stats:** after the crawl (or mid-run via `crawler.stats`), inspect:

| Key                                                | Meaning                                          |
|----------------------------------------------------|--------------------------------------------------|
| `stealth/requests` / `stealth/requests/{driver}`   | Stealth fetches                                  |
| `stealth/responses` / `stealth/responses/{driver}` | Completed responses                              |
| `stealth/successes` / `stealth/successes/{driver}` | Non-banned responses below HTTP 400              |
| `stealth/failures` / `stealth/failures/{driver}`   | Banned responses or HTTP 400+                    |
| `stealth/status/{code}`                            | Response count by HTTP status                    |
| `stealth/bans` / `stealth/bans/{driver}`           | Session-ban responses                            |
| `stealth/recycles` / `stealth/recycles/{driver}`   | Session / Chrome recycles                        |
| `stealth/ban_streak`                               | Current consecutive ban streak                   |
| `stealth/driver`                                   | Last stealth driver used                         |
| `stealth/profile`                                  | Last fingerprint profile used                    |
| `stealth/proxy`                                    | Last proxy as `host:port` (no credentials)       |
| `stealth/proxy/requests/{driver}`                  | Requests sent through a proxy                    |
| `stealth/dns/requests/{driver}`                    | Requests using DNS overrides                     |
| `stealth/dns/hosts`                                | Total pinned hosts applied                       |
| `stealth/dns/active_hosts`                         | Pinned hosts on latest request                   |
| `stealth/fallbacks` / `stealth/fallbacks/{driver}` | Browser escalations from `driver="auto"`         |
| `stealth/fallbacks/method/{method}`                | Fallback count by HTTP method (`get`, `post`, …) |
| `stealth/browser_cookies_exported`                 | Browser cookies merged into Scrapy's jar         |

```python
# e.g. in spider_closed
stats = spider.crawler.stats.get_stats()
print(stats.get("stealth/bans"), stats.get("stealth/recycles"))
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

## 📊 Full spider example

Keep the README short — the complete working spider lives in
[`examples/full_spider.py`](examples/full_spider.py).

It shows:

* middleware + `STEALTH_ENABLED` via `custom_settings` (auto-injects `driver="auto"`, turbo first)
* per-request `basic` / `browser` overrides
* POST requests with JSON body and custom headers (see [POST, headers, and cookies](#-post-headers-and-cookies))
* optional snapshot with `@snapshot`
* ban detection and stealth stats on close

```bash
# from a Scrapy project
scrapy crawl stealth_demo

# or one-off
scrapy runspider examples/full_spider.py
```

Minimal version:

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