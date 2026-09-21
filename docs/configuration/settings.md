# Global settings

Configure scrapy-stealth via **Scrapy settings** (`settings.py` or spider `custom_settings`) or the shared **
`scrapy_stealth.config.config`** object at **module level before the spider runs**.

!!! warning "Timing"
The engine client is created at middleware init. Changes inside `start_requests` or `parse`
have **no effect**. Set config before the spider class or use Scrapy settings.

## Scrapy settings (recommended)

Most options are readable from Scrapy settings and applied in middleware `from_crawler` /
`spider_opened`:

```python
STEALTH_ENABLED = True
STEALTH_DRIVER = "turbo"
STEALTH_PROXIES = ["http://proxy1:8080"]
STEALTH_DNS_OVERRIDES = {"example.com": "203.0.113.10"}
STEALTH_RECYCLE_AFTER_BANS = 5
STEALTH_PROXY_HEALTH = True
STEALTH_LOGS = True
BROWSER_HEADLESS = False
BROWSER_EXECUTABLE_PATH = None
```

## Python config object

```python
from scrapy_stealth.config import config

config.STEALTH_DRIVER = "turbo"
config.HTTP2 = True
config.HTTP3 = False
config.BROWSER_SETTLE_S = 4.0
config.STEALTH_LOGS = False
```

## Settings reference

| Setting                       | Type        | Default   | Description                                                      |
|-------------------------------|-------------|-----------|------------------------------------------------------------------|
| `STEALTH_ENABLED`             | `bool`      | `False`   | Route all requests through stealth; inject `driver="auto"`       |
| `STEALTH_DRIVER`              | `str`       | `"turbo"` | Primary HTTP driver for `auto`: `basic`, `turbo`, `browser`      |
| `STEALTH_PROXIES`             | `list[str]` | `[]`      | Proxy pool; rotated on recycle and transport failure             |
| `STEALTH_DNS_OVERRIDES`       | `dict`      | `{}`      | Host → IP map for all drivers                                    |
| `STEALTH_RECYCLE_AFTER_BANS`  | `int`       | `5`       | Consecutive bans before session recycle                          |
| `STEALTH_PROXY_HEALTH`        | `bool`      | `True`    | Per-proxy + per-domain health scoring                            |
| `STEALTH_PROXY_CIRCUIT_AFTER` | `int`       | `3`       | Failures before proxy cooldown                                   |
| `STEALTH_PROXY_COOLDOWN_S`    | `float`     | `300.0`   | Cooldown duration (seconds)                                      |
| `STEALTH_PROXY_CIRCUIT_CODES` | set         | `{403}`   | Status codes that trip the circuit                               |
| `STEALTH_LOGS`                | `bool`      | `True`    | Styled console + package logger. PyPI update notice always shows |
| `BROWSER_HEADLESS`            | `bool`      | `False`   | Browser driver headless mode                                     |
| `BROWSER_SETTLE_S`            | `float`     | `4.0`     | Seconds to wait for JS after navigation                          |
| `BROWSER_CHALLENGE_TIMEOUT_S` | `float`     | `30.0`    | Max wait on Cloudflare / challenge pages                         |
| `BROWSER_EXECUTABLE_PATH`     | `str`       | `None`    | Custom Chrome/Chromium/Brave binary path                         |
| `BROWSER_EXPORT_COOKIES`      | `bool`      | `True`    | Merge browser tab cookies into Scrapy jar                        |
| `BROWSER_STATIC_ASSETS_BLOCK` | `bool`      | `False`   | Block images/fonts/CSS in browser via CDP                        |
| `BROWSER_PROXY_BYPASS_LIST`   | `list`      | `[]`      | Chrome `--proxy-bypass-list` patterns                            |
| `BROWSER_NO_SANDBOX`          | `bool`      | auto      | Force `--no-sandbox` (Docker/root)                               |
| `BROWSER_MAX_TABS`            | `int`       | `10`      | Max concurrent browser tabs                                      |

## Config object reference

All attributes on `scrapy_stealth.config.config`. Many mirror Scrapy settings above.

| Attribute                     | Type             | Default                   | Description                                                                  |
|-------------------------------|------------------|---------------------------|------------------------------------------------------------------------------|
| `DEFAULT_ENGINE`              | `str`            | `"scrapy"`                | Engine when `meta["stealth"]` is absent                                      |
| `DEFAULT_TIMEOUT`             | `int`            | `30`                      | Stealth request timeout (seconds)                                            |
| `STEALTH_DRIVER`              | `str`            | `"turbo"`                 | Primary HTTP driver for `auto`; also default per-request driver              |
| `STEALTH_ENABLED`             | `bool`           | `False`                   | Route every request through stealth; inject `driver="auto"` unless opted out |
| `HTTP2`                       | `bool`           | `True`                    | HTTP/2 for basic/turbo; override per-request via `meta["stealth"]["http2"]`  |
| `HTTP3`                       | `bool`           | `False`                   | Turbo: HTTP/3 (QUIC); needs UDP-capable proxy                                |
| `BLOCK_CODES`                 | `frozenset[int]` | `{403, 429, 503}`         | HTTP status codes treated as blocked                                         |
| `BLOCK_KEYWORDS`              | `list[str]`      | captcha, access denied, … | Body-text patterns treated as blocked                                        |
| `BROWSER_HEADLESS`            | `bool`           | `False`                   | Browser driver headless mode                                                 |
| `BROWSER_SETTLE_S`            | `float`          | `4.0`                     | Seconds to wait after navigation for JS                                      |
| `BROWSER_CHALLENGE_TIMEOUT_S` | `float`          | `30.0`                    | Max wait on Cloudflare / challenge pages                                     |
| `BROWSER_NO_SANDBOX`          | `bool \| None`   | `None`                    | Disable Chrome sandbox; `None` = auto (root/Docker)                          |
| `BROWSER_EXECUTABLE_PATH`     | `str \| None`    | `None`                    | Browser binary path; `None` = auto-detect Chrome                             |
| `BROWSER_MAX_TABS`            | `int`            | `10`                      | Max concurrent Chrome tabs                                                   |
| `STEALTH_RECYCLE_AFTER_BANS`  | `int`            | `5`                       | Consecutive bans before session recycle                                      |
| `BROWSER_STATIC_ASSETS_BLOCK` | `bool`           | `False`                   | Block images/fonts/CSS via CDP; off when `snapshot=True`                     |
| `BROWSER_EXPORT_COOKIES`      | `bool`           | `True`                    | Merge browser tab cookies into Scrapy jar                                    |
| `BROWSER_PROXY_BYPASS_LIST`   | `list[str]`      | `[]`                      | Chrome `--proxy-bypass-list` (global, launch-time)                           |
| `STEALTH_DNS_OVERRIDES`       | `dict[str, str]` | `{}`                      | Host → IP map for all drivers                                                |
| `STEALTH_PROXIES`             | `list[str]`      | `[]`                      | Proxy pool; rotated on recycle and transport failure                         |
| `STEALTH_PROXY_HEALTH`        | `bool`           | `True`                    | Per-proxy + per-domain health scoring                                        |
| `STEALTH_PROXY_CIRCUIT_AFTER` | `int`            | `3`                       | Failures before proxy cooldown                                               |
| `STEALTH_PROXY_COOLDOWN_S`    | `float`          | `300.0`                   | Cooldown duration (seconds)                                                  |
| `STEALTH_PROXY_CIRCUIT_CODES` | `frozenset[int]` | `{403}`                   | Status codes that trip proxy circuit                                         |
| `STEALTH_LOGS`                | `bool`           | `True`                    | Styled console + package logs; PyPI update notice always shown               |

Read values programmatically:

```python
config.get("DEFAULT_ENGINE")
config.get("MISSING_KEY", "default")
```

## Middleware registration

```python
DOWNLOADER_MIDDLEWARES = {
    "scrapy_stealth.middlewares.StealthDownloaderMiddleware": 950,
}
```

Priority **950** runs after Scrapy's `CookiesMiddleware` (700), so `Request(cookies=...)` and the cookie jar are applied before stealth
handles the request.

## Next

- [Per-request meta](meta.md)
- [Drivers overview](../drivers/overview.md)
