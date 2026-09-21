# scrapy-stealth

**Stealthy Crawling. Maximum Results.**

A pluggable anti-bot and stealth framework for Scrapy — browser impersonation, Smart Proxy Management, fingerprint cycling, and
intelligent retry strategies for production crawls.

## Why scrapy-stealth?

Modern sites use TLS fingerprinting, behavioral detection, rate limits, and IP blocks. scrapy-stealth adds:

- Browser-level impersonation (TLS + HTTP/2 via `turbo`)
- Real Chrome via CDP for JS-heavy pages (`browser`)
- Smart browser selection (`auto` — HTTP first, browser on challenge)
- Adaptive rate limiting and behavioral timing (auto-enabled)
- Smart Proxy Management with per-domain health scoring
- Anti-bot detection (Cloudflare, Akamai, DataDome signals)

## Comparison at a glance

| Feature                   | scrapy-stealth | scrapy-impersonate | scrapy-playwright |
|---------------------------|:--------------:|:------------------:|:-----------------:|
| TLS fingerprint spoofing  |      Yes       |        Yes         |        No         |
| Built-in proxy rotation   |      Yes       |         No         |        No         |
| Smart Proxy Management    |      Yes       |         No         |        No         |
| Per-request engine switch |      Yes       |         No         |        No         |
| Smart `auto` fallback     |      Yes       |         No         |        No         |
| Native Scrapy integration |      Yes       |        Yes         |        Yes        |

## Features

- Pluggable engines: `scrapy` (native) and `stealth` (basic / turbo / browser / auto)
- Per-request control via `request.meta["stealth"]`
- Full request fidelity: POST, cookies, custom headers on all drivers
- Browser cookie handoff to Scrapy's jar
- Cloudflare / Turnstile wait logic on browser driver
- DNS overrides (pin host → IP, keep SNI/Host)
- Snapshot decorator for PNG captures
- Rich Scrapy stats telemetry

## Quick install

```bash
pip install scrapy-stealth
```

Requires **Python 3.11+** and **Scrapy 2.12–2.x**.

## Minimal setup

```python
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
}
STEALTH_ENABLED = True  # injects driver="auto" on every request
```

```python
yield scrapy.Request("https://example.com")
```

See [Quick start](getting-started/quickstart.md) for per-request and global modes.

## Next steps

- [Installation](getting-started/installation.md)
- [Global settings](configuration/settings.md)
- [Drivers overview](drivers/overview.md)
- [Cookies & requests](guides/cookies-and-requests.md)

## Links

- [PyPI](https://pypi.org/project/scrapy-stealth/)
- [GitHub](https://github.com/fawadss1/scrapy-stealth)
- [Changelog](https://github.com/fawadss1/scrapy-stealth/releases)
- [Example spider](https://github.com/fawadss1/scrapy-stealth/blob/master/examples/full_spider.py)
