# Browser engine

The `browser` driver runs **real Chrome** via the Chrome DevTools Protocol (nodriver) — no WebDriver. One persistent browser, **new tab
per request**.

Use for Cloudflare JS challenges, heavy JavaScript, login flows, and when `turbo` returns challenge pages.

The browser driver uses a **visible Chrome window by default** (`BROWSER_HEADLESS = False`). Use
`headless: True` in meta or `BROWSER_HEADLESS = True` in settings only when you need a headless
window (e.g. CI or a server without a display).

## Per-request

```python
yield scrapy.Request(
    "https://example.com",
    meta={
        "stealth": {
            "driver": "browser",
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
        "settle": 12,
    }
}
# Or globally: BROWSER_CHALLENGE_TIMEOUT_S = 45
```

On 403/503 challenge pages, the driver waits up to `BROWSER_CHALLENGE_TIMEOUT_S` (default 30s)
for the challenge to clear.

## External CDP connect

Attach to a browser that is already running instead of launching local Chrome (Fortress,
Brave/Chrome with `--remote-debugging-port`, or any remote CDP service):

```python
# Local debug port (Brave, Chrome, Fortress, etc.)
STEALTH_CDP_URL = "http://127.0.0.1:9222"
# Equivalent: ws://127.0.0.1:9222/  (root ws URL — discovers browser via HTTP, same as above)

# Full WebSocket path (ws://host/devtools/browser/… or …/page/…) — only when you have a
# live URL; copied DevTools browser ids expire. Prefer http://host:9222 or ws://host:9222/.

# Remote HTTPS endpoint with auth headers on /json/version and the WebSocket
STEALTH_CDP_URL = "https://cdp.example.com/v1"
STEALTH_CDP_CONNECT_KWARGS = {
    "headers": {"Authorization": "Bearer YOUR_TOKEN"},
    "timeout": 30,
}
```

Per-request overrides:

```python
meta = {
    "stealth": {
        "driver": "browser",
        "cdp_url": "http://127.0.0.1:9222",
        "cdp_connect_kwargs": {"headers": {"Authorization": "Basic …"}},
    }
}
```

When `STEALTH_CDP_URL` is set, scrapy-stealth **does not** launch Chrome, but it still starts
the **local CONNECT relay** when you use `STEALTH_PROXIES`, `meta["stealth"]["proxy"]`, or
`STEALTH_DNS_OVERRIDES` / `meta["stealth"]["dns"]`. Tabs are opened in a CDP browser context
that points at `http://127.0.0.1:<relay>` so upstream proxy auth and DNS pinning work the
same as with a locally launched browser.

Closing the spider disconnects the CDP session but **does not** terminate the external browser.

### Fortress / Docker on Linux (`ERR_PROXY_CONNECTION_FAILED`)

**Proxy only (no DNS pin):** scrapy-stealth points Fortress **straight at your upstream
proxy** (Oxylabs, etc.) via CDP — no `127.0.0.1` relay. You should see a log line:
`External CDP: using upstream proxy directly`.

**Proxy + DNS pin (or authenticated proxy):** the CONNECT relay runs **next to Scrapy**.
scrapy-stealth picks the advertise IP automatically (your LAN IP, e.g. `10.10.10.178`) and
listens on `0.0.0.0` when using external CDP. Fortress must be able to reach that URL
(firewall / VPN). Local Brave on the same PC still uses `127.0.0.1`.

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
