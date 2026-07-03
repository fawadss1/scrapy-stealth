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

See [CHECK.md](CHECK.md) for individual commands.

## Conventions

- Per-request options live in `request.meta["stealth"]`.
- Global defaults: `STEALTH_ENABLED`, `STEALTH_DRIVER`, `STEALTH_PROXIES` in Scrapy settings, or `scrapy_stealth.config.config`.
- Browser engine uses Chrome via CDP (`nodriver`); proxy mode uses a local auth relay.

---

## Sponsor

**[NodeMaven](https://go.nodemaven.com/Fawadss1agentmd)** — the most reliable proxy provider with the highest-quality IP on the market.
Best solution for automation, web scraping, SEO research, and social media management.

**Why NodeMaven?**

- 99.9% uptime
- Sticky sessions up to 7 days
- IP filtering: all proxies have fraud score <97%
- No KYC required
- Cashback on traffic — burn GB and earn up to 10% back

Special codes for scrapy-stealth users:

- `SCRAPYSTEALTH35` — 35% off Mobile and Residential Proxies
- `SCRAPYSTEALTH40` — 40% off ISP (Static) Proxies
