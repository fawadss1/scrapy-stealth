---
hide:
  - title
---

<div class="hero-panel">
  <div class="hero-panel__inner">
    <img src="static/logo.png" alt="scrapy-stealth logo" class="hero-panel__logo">
    <h1 class="hero-title">scrapy-stealth</h1>
    <p class="hero-tagline">Stealthy Crawling. Maximum Results.</p>
    <p class="hero-desc">
      A pluggable anti-bot and stealth framework for Scrapy — TLS impersonation, behavioral fingerprinting,
      adaptive rate limiting, smart proxies, and real Chrome.
    </p>
    <div class="hero-badges">
      <span class="hero-badge hero-badge--cyan"><i class="fa-brands fa-python"></i> Python 3.11+</span>
      <span class="hero-badge hero-badge--violet"><i class="fa-solid fa-spider"></i> Scrapy 2.12–2.x</span>
      <span class="hero-badge hero-badge--emerald"><i class="fa-solid fa-scale-balanced"></i> MIT License</span>
      <a href="https://pypi.org/project/scrapy-stealth/" target="_blank" class="hero-badge hero-badge--emerald">
        <i class="fa-solid fa-tag"></i> <span class="version-lbl">v…</span>
      </a>
    </div>
  </div>
</div>

## Why scrapy-stealth?

Modern sites use TLS fingerprinting, behavioral detection, rate limits, and IP blocks. scrapy-stealth adds:

<div class="feature-grid" markdown="0">
  <div class="feature-card">
    <div class="feature-card__icon"><i class="fa-solid fa-dna"></i></div>
    <div class="feature-card__body">
      <p class="feature-card__title">Browser-level impersonation</p>
      <p class="feature-card__text">Deep TLS and HTTP/2 fingerprints via the turbo driver.</p>
    </div>
  </div>
  <div class="feature-card">
    <div class="feature-card__icon feature-card__icon--violet"><i class="fa-brands fa-chrome"></i></div>
    <div class="feature-card__body">
      <p class="feature-card__title">Real Chrome via CDP</p>
      <p class="feature-card__text">Full browser engine for JS-heavy pages and challenges.</p>
    </div>
  </div>
  <div class="feature-card">
    <div class="feature-card__icon feature-card__icon--emerald"><i class="fa-solid fa-wand-magic-sparkles"></i></div>
    <div class="feature-card__body">
      <p class="feature-card__title">Smart auto fallback</p>
      <p class="feature-card__text">HTTP first, browser on challenge — per request.</p>
    </div>
  </div>
  <div class="feature-card">
    <div class="feature-card__icon"><i class="fa-solid fa-globe"></i></div>
    <div class="feature-card__body">
      <p class="feature-card__title">Smart proxy management</p>
      <p class="feature-card__text">Per-domain health scoring, cooldown, and failover.</p>
    </div>
  </div>
</div>

## Comparison at a glance

| Feature                   | scrapy-stealth | scrapy-impersonate | scrapy-playwright |
|---------------------------|:--------------:|:------------------:|:-----------------:|
| TLS fingerprint spoofing  |      Yes       |        Yes         |        No         |
| Built-in proxy rotation   |      Yes       |         No         |        No         |
| Smart Proxy Management    |      Yes       |         No         |        No         |
| Per-request engine switch |      Yes       |         No         |        No         |
| Smart `auto` fallback     |      Yes       |         No         |        No         |
| Native Scrapy integration |      Yes       |        Yes         |        Yes        |

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
- [Changelog](reference/changelog.md)
- [Example spider](https://github.com/fawadss1/scrapy-stealth/blob/master/examples/full_spider.py)
