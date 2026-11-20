# scrapy-stealth — agent guide

Pluggable anti-bot and stealth framework for Scrapy. Python 3.11+, Scrapy 2.12–2.x.

## Layout

- `scrapy_stealth/middlewares/` — Scrapy downloader middleware entry point
- `scrapy_stealth/engines/` — request engines (`scrapy`, `basic`, `turbo`, `browser`)
- `scrapy_stealth/strategies/` — proxy, fingerprint, and retry helpers
- `scrapy_stealth/detectors/` — anti-bot / block detection
- `scrapy_stealth/config.py` — module-level defaults (must be set before spider runs)
- `tests/` — pytest suite

## Local checks

```bash
pip install -e ".[dev]"
python scripts/check.py
```

See [CHECK.md](CHECK.md) for individual commands. User docs: [scrapy-stealth.readthedocs.io](https://scrapy-stealth.readthedocs.io/)
(source in `docs/`, built via MkDocs).

## Conventions

- Per-request options live in `request.meta["stealth"]`.
- Global defaults: `STEALTH_ENABLED`, `STEALTH_DRIVER`, `STEALTH_PROXIES` in Scrapy settings, or `scrapy_stealth.config.config`.
- Browser engine uses Chrome via CDP (`nodriver`); proxy mode uses a local auth relay.

---

## Sponsors

### NodeMaven

**[NodeMaven](https://go.nodemaven.com/scrapystealthagentmdoctober)** — the most efficient proxy provider for web scrapping and automation with
the highest-quality IP on the market.

**Why [NodeMaven](https://go.nodemaven.com/scrapystealthagentmdoctober)?**

- 99.9% uptime
- ZIP Targeting
- IP filtering: all proxies have fraud score <97%
- No KYC required
- Unique free tools: [Proxy Bandwidth Checker](https://go.nodemaven.com/scrapystealthtoolsoctober), Meta Tag Checker, IP Lookup, and others

Special codes for scrapy-stealth users:

- `SCRAPYSTEALTH35` — 35% off Mobile and Residential Proxies
- `SCRAPYSTEALTH40` — 40% off ISP (Static) Proxies
- `SCRAPYSTEALTH2X` — 2X traffic for Black Friday

### CyberYozh App

**[CyberYozh App](https://app.cyberyozh.com/?utm_source=github&utm_medium=sponsorship&utm_campaign=scrapy_stealth)** —
Operational proxy infrastructure for web scraping, browser automation, SEO, and multi-account workflows.

**Why [CyberYozh App](https://app.cyberyozh.com/?utm_source=github&utm_medium=sponsorship&utm_campaign=scrapy_stealth)?**

- Mobile LTE/5G (unlimited traffic), [Residential](https://app.cyberyozh.com/proxy/residential-rotating/?utm_source=github&utm_medium=sponsorship&utm_campaign=scrapy_stealth), Static ISP, and Datacenter proxies
- 100M+ IPs across 195+ countries with free geo-targeting
- 24-hour sticky sessions, per-request rotation, and traffic rollover
- 99.9% proxy uptime with HTTP(S), SOCKS5, UDP, VLESS, and OpenVPN support
- Built-in tools: [Fraud Score checks](https://app.cyberyozh.com/checkers/?utm_source=github&utm_medium=sponsorship&utm_campaign=scrapy_stealth) (IP, phone, card), SMS activation, virtual cards, and Android Cloud Phones
