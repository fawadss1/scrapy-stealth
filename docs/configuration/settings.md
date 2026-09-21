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

## Config-only attributes

These live on `scrapy_stealth.config.config` (some also mirror Scrapy settings):

| Attribute         | Default         | Description                          |
|-------------------|-----------------|--------------------------------------|
| `DEFAULT_ENGINE`  | `"scrapy"`      | Engine when `meta["stealth"]` absent |
| `DEFAULT_TIMEOUT` | `30`            | Request timeout (seconds)            |
| `HTTP2`           | `True`          | HTTP/2 for basic/turbo               |
| `HTTP3`           | `False`         | HTTP/3 (QUIC) for turbo              |
| `BLOCK_CODES`     | `{403,429,503}` | Status codes treated as blocked      |
| `BLOCK_KEYWORDS`  | list            | Body text patterns for blocks        |

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
- [Global settings in README](https://github.com/fawadss1/scrapy-stealth/blob/master/README.md#-global-configuration) (extended table
  on GitHub)
