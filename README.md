<p align="center">
  <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/logo.png" alt="scrapy-stealth logo" width="720" style="border-radius: 1.25rem;"/>
</p>

<h1 align="center">scrapy-stealth</h1>

<p align="center"><strong>Stealthy Crawling. Maximum Results.</strong></p>

<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=DM+Sans&weight=600&size=22&duration=3500&pause=1200&color=22D3EE&center=true&vCenter=true&width=640&height=36&lines=Pluggable+anti-bot+middleware+for+Scrapy;TLS+%C2%B7+smart+proxies+%C2%B7+external+CDP+%C2%B7+Chrome" alt="Pluggable anti-bot middleware for Scrapy — TLS, smart proxies, external CDP, Chrome"/>
</p>

<p align="center">Per-request drivers and automatic HTTP → browser fallback.</p>

[![Documentation](https://readthedocs.org/projects/scrapy-stealth/badge/?version=latest)](https://scrapy-stealth.readthedocs.io/en/latest/)
[![PyPI version](https://img.shields.io/pypi/v/scrapy-stealth?color=blue)](https://pypi.org/project/scrapy-stealth/)
[![Downloads](https://static.pepy.tech/badge/scrapy-stealth)](https://pepy.tech/project/scrapy-stealth)
[![Python versions](https://img.shields.io/pypi/pyversions/scrapy-stealth)](https://pypi.org/project/scrapy-stealth/)
[![GitHub release](https://img.shields.io/github/v/release/fawadss1/scrapy-stealth)](https://github.com/fawadss1/scrapy-stealth/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](https://github.com/fawadss1/scrapy-stealth/blob/master/LICENSE)
[![Changelog](https://img.shields.io/badge/changelog-docs-informational)](https://scrapy-stealth.readthedocs.io/en/latest/reference/changelog/)

`scrapy-stealth` adds TLS impersonation, behavioral fingerprinting, adaptive rate limiting, smart proxies, and real Chrome to Scrapy —
with per-request driver selection and automatic HTTP → browser fallback.

**Documentation:** [scrapy-stealth.readthedocs.io/en/latest/](https://scrapy-stealth.readthedocs.io/en/latest/)

---

<details>
<summary><h3>💜 Sponsors</h3></summary>

<table>
  <tr>
    <td colspan="2" align="center">
      <a href="https://go.nodemaven.com/scrapystealthreadmeoctober">
        <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/sponsors/nodemaven-banner.png" alt="NodeMaven — Best proxy for web scrapping and automation with the highest quality IP" width="720"/>
      </a>
    </td>
  </tr>
  <tr>
    <td colspan="2">
      <strong><a href="https://go.nodemaven.com/scrapystealthreadmeoctober">NodeMaven</a></strong> — the most efficient proxy provider for web scrapping and automation with the highest-quality IP on the market.
      <br/><br/>
      <strong>Why <a href="https://go.nodemaven.com/scrapystealthreadmeoctober">NodeMaven</a>?</strong>
      <ul>
        <li>99.9% uptime</li>
        <li>ZIP Targeting</li>
        <li>IP filtering: all proxies have fraud score &lt;97%</li>
        <li>No KYC required</li>
        <li>Unique free tools: <a href="https://go.nodemaven.com/scrapystealthtoolsoctober">Proxy Bandwidth Checker</a>, Meta Tag Checker, IP Lookup, and others</li>
      </ul>
      Special codes for scrapy-stealth users:
      <code>SCRAPYSTEALTH35</code> — 35% off Mobile and Residential Proxies;
      <code>SCRAPYSTEALTH40</code> — 40% off ISP (Static) Proxies;
      <code>SCRAPYSTEALTH2X</code> — 2X traffic for Black Friday.
    </td>
  </tr>
  <tr>
    <td colspan="2" align="center">
      <a href="https://app.cyberyozh.com/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">
        <img src="https://raw.githubusercontent.com/fawadss1/scrapy-stealth/master/docs/static/sponsors/cyberyozh-banner.png" alt="CyberYozh App — Operational proxy infrastructure for web scraping and automation" width="720"/>
      </a>
    </td>
  </tr>
  <tr>
    <td colspan="2">
      <strong><a href="https://app.cyberyozh.com/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">CyberYozh App</a></strong> — Operational proxy infrastructure for web scraping, browser automation, SEO, and multi-account workflows.
      <br/><br/>
      <strong>Why <a href="https://app.cyberyozh.com/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">CyberYozh App</a>?</strong>
      <ul>
        <li>Mobile LTE/5G (unlimited traffic), <a href="https://app.cyberyozh.com/proxy/residential-rotating/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">Residential</a>, Static ISP, and Datacenter proxies</li>
        <li>100M+ IPs across 195+ countries with free geo-targeting</li>
        <li>24-hour sticky sessions, per-request rotation, and traffic rollover</li>
        <li>99.9% proxy uptime with HTTP(S), SOCKS5, UDP, VLESS, and OpenVPN support</li>
        <li>Built-in tools: <a href="https://app.cyberyozh.com/checkers/?utm_source=github&amp;utm_medium=sponsorship&amp;utm_campaign=scrapy_stealth">Fraud Score checks</a> (IP, phone, card), SMS activation, virtual cards, and Android Cloud Phones</li>
      </ul>
    </td>
  </tr>
</table>

</details>

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
