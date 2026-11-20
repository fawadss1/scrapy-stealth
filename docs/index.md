---
hide:
  - title
---

<div class="hero-panel">
  <div class="hero-panel__inner">
    <img src="static/logo.png" alt="scrapy-stealth logo" class="hero-panel__logo" style="border-radius: 1.25rem;">
    <h1 class="hero-title">scrapy-stealth</h1>
    <p class="hero-tagline">Stealthy Crawling. Maximum Results.</p>
    <p class="hero-typing">
      <img src="https://readme-typing-svg.demolab.com?font=DM+Sans&weight=600&size=22&duration=3500&pause=1200&color=22D3EE&center=true&vCenter=true&width=640&height=36&lines=Pluggable+anti-bot+middleware+for+Scrapy;TLS+%C2%B7+smart+proxies+%C2%B7+external+CDP+%C2%B7+Chrome" alt="Pluggable anti-bot middleware for Scrapy — TLS, smart proxies, external CDP, Chrome"/>
    </p>
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

## Sponsors

<div class="sponsor-stack" markdown="0">
  <section class="sponsor-panel">
    <a class="sponsor-panel__banner" href="https://go.nodemaven.com/scrapystealthreadmeoctober">
      <img src="static/sponsors/nodemaven-banner.png" alt="NodeMaven — proxy provider for web scrapping and automation" width="720" height="90" loading="lazy" decoding="async"/>
    </a>
    <p class="sponsor-panel__lead">
      <strong><a href="https://go.nodemaven.com/scrapystealthreadmeoctober">NodeMaven</a></strong> — the most efficient proxy provider for web scrapping and automation with the highest-quality IP on the market.
    </p>
    <p class="sponsor-panel__subtitle"><strong>Why <a href="https://go.nodemaven.com/scrapystealthreadmeoctober">NodeMaven</a>?</strong></p>
    <ul class="sponsor-panel__list">
      <li>99.9% uptime</li>
      <li>ZIP Targeting</li>
      <li>IP filtering: all proxies have fraud score &lt;97%</li>
      <li>No KYC required</li>
      <li>Unique free tools: <a href="https://go.nodemaven.com/scrapystealthtoolsoctober">Proxy Bandwidth Checker</a>, Meta Tag Checker, IP Lookup, and others</li>
    </ul>
    <p class="sponsor-panel__codes">
      Special codes: <code>SCRAPYSTEALTH35</code> (35% off Mobile and Residential);
      <code>SCRAPYSTEALTH40</code> (40% off ISP Static);
      <code>SCRAPYSTEALTH2X</code> (2X traffic for Black Friday).
    </p>
  </section>
  <section class="sponsor-panel">
    <a class="sponsor-panel__banner" href="https://app.cyberyozh.com/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">
      <img src="static/sponsors/cyberyozh-banner.png" alt="CyberYozh App — Operational proxy infrastructure for web scraping and automation" width="720" height="90" loading="lazy" decoding="async"/>
    </a>
    <p class="sponsor-panel__lead">
      <strong><a href="https://app.cyberyozh.com/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">CyberYozh App</a></strong> — Operational proxy infrastructure for web scraping, browser automation, SEO, and multi-account workflows.
    </p>
    <p class="sponsor-panel__subtitle"><strong>Why <a href="https://app.cyberyozh.com/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">CyberYozh App</a>?</strong></p>
    <ul class="sponsor-panel__list">
      <li>Mobile LTE/5G (unlimited traffic), <a href="https://app.cyberyozh.com/proxy/residential-rotating/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">Residential</a>, Static ISP, and Datacenter proxies</li>
      <li>100M+ IPs across 195+ countries with free geo-targeting</li>
      <li>24-hour sticky sessions, per-request rotation, and traffic rollover</li>
      <li>99.9% proxy uptime with HTTP(S), SOCKS5, UDP, VLESS, and OpenVPN support</li>
      <li>Built-in tools: <a href="https://app.cyberyozh.com/checkers/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">Fraud Score checks</a> (IP, phone, card), SMS activation, virtual cards, and Android Cloud Phones</li>
    </ul>
  </section>
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

See the [full comparison table](reference/comparison.md) and [feature list](reference/features.md).

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
- [Quick start](getting-started/quickstart.md)
- [Example spider](getting-started/example-spider.md)
- [Global settings](configuration/settings.md)
- [Drivers overview](drivers/overview.md)
- [Cookies & requests](guides/cookies-and-requests.md)

## Links

- [PyPI](https://pypi.org/project/scrapy-stealth/)
- [GitHub](https://github.com/fawadss1/scrapy-stealth)
- [Changelog](reference/changelog.md)
- [Example spider](https://github.com/fawadss1/scrapy-stealth/blob/master/examples/full_spider.py)
