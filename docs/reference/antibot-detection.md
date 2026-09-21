# Anti-bot detection

scrapy-stealth classifies blocked or challenged responses using HTTP status codes, body keywords, and known CDN / WAF patterns.

The middleware uses this internally for ban streaks, session recycle, proxy health, and `driver="auto"` fallback. You can also call the detector from spiders:

```python
from scrapy_stealth.detectors.antibot import AntiBotDetector

detector = AntiBotDetector()

if detector.is_blocked(response):
    self.logger.warning("Blocked: %s", response.url)
```

## Defaults

Configured on `scrapy_stealth.config.config`:

| Setting          | Default                         | Role                          |
|------------------|---------------------------------|-------------------------------|
| `BLOCK_CODES`    | `{403, 429, 503}`               | HTTP statuses treated as bans |
| `BLOCK_KEYWORDS` | `captcha`, `access denied`, …   | Body text patterns            |

Extend at module level before the spider runs:

```python
from scrapy_stealth.config import config

config.BLOCK_CODES |= {407}
config.BLOCK_KEYWORDS.append("banned")
```

## What triggers `driver="auto"` fallback

Phase 1 (`basic` / `turbo`) escalates to browser when the response looks like a JS challenge or session ban — e.g. Cloudflare interstitials, Turnstile, Akamai/DataDome body signatures, or repeated blocks.

See [Smart selection (auto)](../drivers/auto.md).

## Related

- [Troubleshooting](troubleshooting.md)
- [Global settings](../configuration/settings.md)
