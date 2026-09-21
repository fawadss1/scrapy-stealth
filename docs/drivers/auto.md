# Smart selection (`auto`)

`driver="auto"` picks the right engine per response: fast HTTP first, real Chrome only when needed.

When `STEALTH_ENABLED = True`, the middleware injects `driver="auto"` automatically.

## Phases

| Phase | Driver                       | When                                            |
|-------|------------------------------|-------------------------------------------------|
| 1     | `turbo` (default) or `basic` | First attempt — low memory, high throughput     |
| 2     | `browser` (`headless=False`) | One retry when phase 1 is blocked or challenged |

Phase 2 always opens a **visible Chrome window** for better evasion, regardless of
`BROWSER_HEADLESS`.

## Setup

```python
# Global — simplest
STEALTH_ENABLED = True
STEALTH_DRIVER = "turbo"  # optional: use "basic" for lighter HTTP

# Per-request
yield scrapy.Request(url, meta={"stealth": {"driver": "auto"}})
```

## Variants

```python
# Always browser — skip phase 1
meta = {"stealth": {"driver": "browser"}}

# HTTP only — no browser retry
meta = {"stealth": {"driver": "turbo"}}

# Keep auto but disable browser fallback
meta = {"stealth": {"driver": "auto", "fallback": False}}
```

## What triggers fallback

Signals include HTTP 403/429/503, Cloudflare interstitials (“Just a moment”), Turnstile pages, Akamai/DataDome body patterns, and other
anti-bot detector matches.

Each request is retried **at most once**. If the browser fetch also fails, the original HTTP response is returned.

## Stats

- `stealth/fallbacks` — total browser escalations
- `stealth/fallbacks/browser` — by driver
- `stealth/fallbacks/method/post` — by HTTP method

## POST with auto

Phase 1 sends POST via `turbo`/`basic`. If challenged, phase 2 retries with **browser** using the same method, body, and headers (form
hidden fields merged for urlencoded login flows).

See [Cookies & HTTP requests](../guides/cookies-and-requests.md).
