# Throttle & behavior

Two features run **automatically** on every stealth request — no settings or meta flags.

## Adaptive rate limiting

Per-domain AIMD throttle on all drivers:

- **HTTP 429 / `Retry-After`** — increases spacing, honors retry header
- **Success streaks** — spacing eases back down
- **High latency EMA** — nudges spacing up slightly

403/503 blocks use ban detection and proxy health — throttle learns from rate limits only, not generic bans.

### Stats

- `stealth/throttle/waits`
- `stealth/throttle/wait_ms`
- `stealth/throttle/rate_limited`
- `stealth/throttle/retry_after`

## Behavioral fingerprinting

| Driver    | What runs                                                           |
|-----------|---------------------------------------------------------------------|
| `browser` | Viewport + CDP mouse path + scroll + occasional key nudge after GET |
| `basic`   | Profile-seeded pre-request delay (~30–350 ms) + adaptive throttle   |
| `turbo`   | Same timing as `basic`                                              |

Verify browser behavior on an HTML page with a visible window:

```python
yield scrapy.Request(
    "https://example.com",
    meta={"stealth": {"driver": "browser", "headless": False, "settle": 8}},
)
```

Advanced: `scrapy_stealth.behaviors.simulate_hover(page, x1, y1, x2, y2)` for custom CDP paths.

!!! note Behavioral replay does not bypass IP blocks. For CDN assets without JS challenges, prefer
`driver="turbo"` with a clean proxy.
