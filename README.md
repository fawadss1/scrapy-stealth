<p align="center">
  <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/logo.png" alt="scrapy-stealth logo" width="720"/>
</p>

<h1 align="center">scrapy-stealth</h1>

<p align="center"><strong>Stealthy Crawling. Maximum Results.</strong></p>

<p align="center">A pluggable anti-bot and stealth framework for Scrapy.</p>

[![Documentation](https://readthedocs.org/projects/scrapy-stealth/badge/?version=latest)](https://scrapy-stealth.readthedocs.io/en/latest/)
[![PyPI version](https://img.shields.io/pypi/v/scrapy-stealth?color=blue)](https://pypi.org/project/scrapy-stealth/)
[![Python versions](https://img.shields.io/pypi/pyversions/scrapy-stealth)](https://pypi.org/project/scrapy-stealth/)
[![GitHub release](https://img.shields.io/github/v/release/fawadss1/scrapy-stealth)](https://github.com/fawadss1/scrapy-stealth/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/fawadss1/scrapy-stealth/blob/master/LICENSE)
[![Changelog](https://img.shields.io/badge/changelog-docs-informational)](https://scrapy-stealth.readthedocs.io/en/latest/reference/changelog/)

`scrapy-stealth` adds TLS impersonation, behavioral fingerprinting, adaptive rate limiting, smart proxies, and real Chrome to Scrapy —
with per-request driver selection and automatic HTTP → browser fallback.

**Documentation:** [scrapy-stealth.readthedocs.io/en/latest/](https://scrapy-stealth.readthedocs.io/en/latest/)

---

## 💜 Sponsors

<table>
  <tr>
    <td colspan="2" align="center">
      <a href="https://go.nodemaven.com/Fawadss1readmesept">
        <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/sponsors/nodemaven-banner.png" alt="NodeMaven — Best proxy for web scrapping and automation with the highest quality IP" width="720"/>
      </a>
    </td>
  </tr>
  <tr>
    <td colspan="2">
      <strong><a href="https://go.nodemaven.com/Fawadss1readmesept">NodeMaven</a></strong> — the most efficient proxy provider for web scrapping and automation with the highest-quality IP on the market.
      <br/><br/>
      <strong>Why <a href="https://go.nodemaven.com/Fawadss1readmesept">NodeMaven</a>?</strong>
      <ul>
        <li>99.9% uptime</li>
        <li>ZIP Targeting</li>
        <li>IP filtering: all proxies have fraud score &lt;97%</li>
        <li>No KYC required</li>
        <li>Unique free tools: <a href="https://go.nodemaven.com/Fawadss1toolssept">Proxy Bandwidth Checker</a>, Meta Tag Checker, IP Lookup, and others</li>
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
      <strong><a href="https://proxy-seller.com/?utm_source=github&utm_medium=referral&utm_campaign=partner_promo&utm_term=github&partner=C2796BDED58F4875">Proxy-Seller</a></strong> — residential, ISP, mobile, IPv4, and IPv6 proxies across 220+ locations. HTTP(S) and SOCKS5, flexible rotation, and 24/7 support.
      <br/><br/>
      Use code <code>FAWAD15</code> at <a href="https://proxy-seller.com/?utm_source=github&utm_medium=referral&utm_campaign=partner_promo&utm_term=github&partner=C2796BDED58F4875">proxy-seller.com</a>.
    </td>
  </tr>
</table>

---

## Install

```bash
pip install scrapy-stealth
```

Requires **Python 3.11+** and **Scrapy 2.12–2.x**. See
the [installation guide](https://scrapy-stealth.readthedocs.io/en/latest/getting-started/installation/).

---

## Quick setup

```python
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
}
STEALTH_ENABLED = True  # injects driver="auto" on every request
```

```python
yield scrapy.Request("https://example.com")
```

That runs **`turbo`** first, then retries once with visible Chrome on JS challenges or session bans.
See [Quick start](https://scrapy-stealth.readthedocs.io/en/latest/getting-started/quickstart/) for per-request mode, proxies, and
`custom_settings`.

---

## Documentation

| Topic           | Link                                                                                                                                                                                                                                                                                                                                                     |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Getting started | [Installation](https://scrapy-stealth.readthedocs.io/en/latest/getting-started/installation/) · [Quick start](https://scrapy-stealth.readthedocs.io/en/latest/getting-started/quickstart/) · [Example spider](https://scrapy-stealth.readthedocs.io/en/latest/getting-started/example-spider/)                                                           |
| Configuration   | [Global settings](https://scrapy-stealth.readthedocs.io/en/latest/configuration/settings/) · [Per-request meta](https://scrapy-stealth.readthedocs.io/en/latest/configuration/meta/)                                                                                                                                                                     |
| Drivers         | [Overview](https://scrapy-stealth.readthedocs.io/en/latest/drivers/overview/) · [Auto](https://scrapy-stealth.readthedocs.io/en/latest/drivers/auto/) · [Browser](https://scrapy-stealth.readthedocs.io/en/latest/drivers/browser/)                                                                                                                      |
| Guides          | [Cookies & requests](https://scrapy-stealth.readthedocs.io/en/latest/guides/cookies-and-requests/) · [Proxies](https://scrapy-stealth.readthedocs.io/en/latest/guides/proxy-management/) · [DNS](https://scrapy-stealth.readthedocs.io/en/latest/guides/dns-overrides/) · [Snapshots](https://scrapy-stealth.readthedocs.io/en/latest/guides/snapshots/) |
| Reference       | [Features](https://scrapy-stealth.readthedocs.io/en/latest/reference/features/) · [Comparison](https://scrapy-stealth.readthedocs.io/en/latest/reference/comparison/) · [Stats](https://scrapy-stealth.readthedocs.io/en/latest/reference/stats/) · [Changelog](https://scrapy-stealth.readthedocs.io/en/latest/reference/changelog/)                    |

---

## Contributing

See [CONTRIBUTING.md](https://github.com/fawadss1/scrapy-stealth/blob/master/CONTRIBUTING.md).

## License

MIT — see [LICENSE](https://github.com/fawadss1/scrapy-stealth/blob/master/LICENSE).
