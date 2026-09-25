# Per-request meta

All per-request options live in `request.meta["stealth"]` as a **dict**.

- **Present dict** → stealth engine handles the request
- **Absent** → default Scrapy downloader (unless `STEALTH_ENABLED = True`)
- **`meta={"stealth": False}`** → opt out when global stealth is on

## Example

```python
yield scrapy.Request(
    "https://example.com/item/1",
    meta={
        "stealth": {
            "driver": "turbo",
            "proxy": "http://user:pass@proxy.example.com:8080",
            "stealth_timeout": 60,
            "http2": True,
            "dns": "203.0.113.10",
        }
    },
)
```

## Meta keys

| Key                   | Type            | Description                                                        |
|-----------------------|-----------------|--------------------------------------------------------------------|
| `driver`              | `str`           | `basic`, `turbo`, `browser`, or `auto`                             |
| `fallback`            | `bool`          | `False` disables browser retry when `driver="auto"`                |
| `profile`             | `str`           | Pin fingerprint (e.g. `chrome150`). Omit for random pool           |
| `proxy`               | `str`           | Explicit proxy URL. `None` = direct, no proxy                      |
| `dns`                 | `str` or `dict` | Per-request DNS override (IP or host map)                          |
| `stealth_timeout`     | `int`           | Timeout in seconds (default 30)                                    |
| `http2`               | `bool`          | HTTP/2 vs HTTP/1.1                                                 |
| `http3`               | `bool`          | Turbo only: HTTP/3 (QUIC)                                          |
| `headless`            | `bool`          | Browser only: `True` = headless; default **visible** window        |
| `settle`              | `float`         | Browser only: JS settle time after load                            |
| `snapshot`            | `bool`          | Browser only: full-page PNG in `response.meta["snapshot_content"]` |
| `static_assets_block` | `bool`          | Browser only: block images/fonts/CSS                               |
| `export_cookies`      | `bool`          | Browser only: merge tab cookies into Scrapy jar                    |

## Browser response meta

After a browser fetch:

| Key                                                 | Type         | Description                |
|-----------------------------------------------------|--------------|----------------------------|
| `response.meta["stealth"]["browser_cookies"]`       | `list[dict]` | Cookies from the tab       |
| `response.meta["stealth"]["browser_cookie_header"]` | `str`        | Ready-made `Cookie` header |

## Cookies on the Request

Use normal Scrapy cookie APIs — stealth forwards them on all drivers:

```python
yield scrapy.Request(
    "https://example.com",
    cookies={"session_id": "abc123"},
    meta={"stealth": {"driver": "turbo"}},
)
```

With `COOKIES_ENABLED = True` (default), Scrapy's `CookiesMiddleware` merges jar + `cookies=`
into the `Cookie` header before stealth runs. scrapy-stealth also reads `request.cookies`
directly as a fallback.

!!! tip
`STEALTH_LOGS` and other global flags belong in **settings**, not in `request.meta`.

## Next

- [Drivers overview](../drivers/overview.md)
- [Cookies guide](../guides/cookies-and-requests.md)
