# Drivers overview

The stealth engine supports four drivers, selected via `meta["stealth"]["driver"]` or
`STEALTH_DRIVER` / `STEALTH_ENABLED`.

| Driver    | Speed    | Use case                                                      |
|-----------|----------|---------------------------------------------------------------|
| `basic`   | Fast     | Light HTTP impersonation via `wreq`                           |
| `turbo`   | Fast     | Deep TLS + HTTP/2 impersonation via `curl_cffi` (**default**) |
| `browser` | Slow     | Real Chrome via CDP — JS, Cloudflare, heavy sites             |
| `auto`    | Adaptive | `turbo`/`basic` first, one `browser` retry on challenge/ban   |

## When to use which

```python
# Default production path (also injected by STEALTH_ENABLED)
meta = {"stealth": {"driver": "auto"}}

# Maximum throughput, no browser cost
meta = {"stealth": {"driver": "turbo"}}

# Always real browser
meta = {"stealth": {"driver": "browser", "headless": False}}

# Lightest HTTP client
meta = {"stealth": {"driver": "basic"}}
```

## Driver capabilities

| Feature                     |  basic  |       turbo        |       browser       |
|-----------------------------|:-------:|:------------------:|:-------------------:|
| GET / HEAD                  |   Yes   |        Yes         |         Yes         |
| POST / PUT / PATCH / DELETE |   Yes   |        Yes         | Yes (in-page fetch) |
| TLS fingerprint             | Profile |  curl-impersonate  |     Real Chrome     |
| HTTP/2                      |   Yes   |        Yes         |         Yes         |
| HTTP/3 (QUIC)               |   No    | Yes (`http3=True`) |         No          |
| JS rendering                |   No    |         No         |         Yes         |
| Cookies / headers           |   Yes   |        Yes         |         Yes         |
| Snapshots                   |   No    |         No         |         Yes         |
| Behavioral timing           |  Auto   |        Auto        |  CDP mouse/scroll   |

## HTTP vs browser

- **`basic` / `turbo`**: ~1–2 s per page, low memory — use for bulk catalog crawling
- **`browser`**: ~5–15 s per page, Chrome process — use for login, challenges, JS-only content
- **`auto`**: Best of both — only pays browser cost when HTTP fails or is challenged

## Session recycle

After `STEALTH_RECYCLE_AFTER_BANS` consecutive banned responses:

- **browser** — restarts Chrome (fresh fingerprint, cookies, CDP)
- **basic / turbo** — clears cached HTTP sessions, rotates profile + proxy

One clean response resets the streak.

## Next

- [Smart selection (`auto`)](auto.md)
- [Browser engine](browser.md)
