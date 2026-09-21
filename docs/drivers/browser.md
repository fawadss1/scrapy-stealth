# Browser engine

The `browser` driver runs **real Chrome** via the Chrome DevTools Protocol (nodriver) — no WebDriver. One persistent browser, **new tab
per request**.

Use for Cloudflare JS challenges, heavy JavaScript, login flows, and when `turbo` returns challenge pages.

## Per-request

```python
yield scrapy.Request(
    "https://example.com",
    meta={
        "stealth": {
            "driver": "browser",
            "headless": False,
            "settle": 4.0,
        }
    },
)
```

## Cloudflare / heavy challenges

```python
meta = {
    "stealth": {
        "driver": "browser",
        "headless": False,
        "settle": 12,
    }
}
# Or globally: BROWSER_CHALLENGE_TIMEOUT_S = 45
```

On 403/503 challenge pages, the driver waits up to `BROWSER_CHALLENGE_TIMEOUT_S` (default 30s)
for the challenge to clear.

## Custom browser binary

```python
BROWSER_EXECUTABLE_PATH = "/usr/bin/brave-browser"
# Windows: r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
```

When `None`, scrapy-stealth auto-detects Chrome/Chromium. A clear error is raised if the path is invalid.

## Behavioral fingerprinting (auto-enabled)

No settings or meta flags — built into the driver:

| Driver            | Behavior                                                                        |
|-------------------|---------------------------------------------------------------------------------|
| `browser`         | Viewport emulation, CDP mouse path, scroll, occasional keyboard nudge after GET |
| `basic` / `turbo` | Profile-seeded pre-request delay (~30–350 ms)                                   |

## Static asset blocking

```python
BROWSER_STATIC_ASSETS_BLOCK = True
# or per-request:
meta = {"stealth": {"static_assets_block": True}}
```

Always disabled when `snapshot=True`.

## CDN / binary URLs

Direct GET to `.jpg`, `.png`, etc. returns **raw bytes** in `response.body` when the origin serves the file. For CDN assets behind
Cloudflare, try `turbo` first; use `browser` when JS clearance is required.

```python
yield scrapy.Request(
    "https://cdn.example.com/media/item-8145.jpg",
    meta={"stealth": {"driver": "turbo"}},
    callback=self.save_image,
)
```

## Docker

```python
BROWSER_NO_SANDBOX = True
BROWSER_EXECUTABLE_PATH = "/usr/bin/chromium"
```

Chrome requires `--no-sandbox` when running as root (auto-detected).

## Proxy bypass list

```python
BROWSER_PROXY_BYPASS_LIST = ["example.com", "*.internal.net", "<local>"]
```

Chrome launch flag — global only, applies when a proxy is configured.

## Performance

Browser mode is **5–10× slower** than turbo. Prefer `driver="auto"` so only challenged URLs hit Chrome.
