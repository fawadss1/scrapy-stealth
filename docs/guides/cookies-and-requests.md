# Cookies & HTTP requests

All stealth drivers honor the same Scrapy `Request` fields: **method**, **body**, **cookies**, and **custom headers**.

Internally, `build_stealth_request()` normalizes each request. Fingerprint headers (`User-Agent`,
`Accept`, `sec-ch-ua`, …) are managed by the impersonation layer — set application headers only (`Content-Type`, `Cookie`,
`Authorization`, …).

## JSON POST

```python
import json

yield scrapy.Request(
    "https://api.example.com/search",
    method="POST",
    body=json.dumps({"search": "laptop", "page": 1}).encode(),
    headers={"Content-Type": "application/json"},
    meta={"stealth": {"driver": "turbo"}},
)
```

With `STEALTH_ENABLED = True`, omit `meta` — same request shape applies.

## Form POST (login)

```python
from urllib.parse import urlencode

yield scrapy.Request(
    "https://app.example.com/login",
    method="POST",
    body=urlencode({"username": "admin", "password": "admin"}).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    meta={"stealth": {"driver": "browser"}},
)
```

The browser driver loads the login page first and merges hidden `<form>` fields (e.g. CSRF tokens)
into urlencoded bodies before in-page `fetch()`.

## Cookies via `Request(cookies=...)`

```python
yield scrapy.Request(
    "https://example.com/dashboard",
    cookies={"session_id": "abc123", "user-settings": "%7B...%7D"},
    meta={"stealth": {"driver": "turbo"}},
)
```

Requirements:

- `COOKIES_ENABLED = True` (Scrapy default)
- Do not set `meta={"dont_merge_cookies": True}` unless intentional

scrapy-stealth merges `Request.cookies` with the `Cookie` header; explicit request cookies win on name clashes.

## Cookie header

```python
yield scrapy.Request(
    "https://example.com",
    headers={
        "Cookie": "session_id=abc123",
        "Authorization": "Bearer token",
    },
    meta={"stealth": {"driver": "turbo"}},
)
```

## Browser cookie handoff

After a browser request, tab cookies are exposed on the response and optionally merged into Scrapy's jar
(`BROWSER_EXPORT_COOKIES = True` by default).

```python
def after_login(self, response):
    stealth = response.meta.get("stealth") or {}
    self.logger.info("cookies: %s", stealth.get("browser_cookie_header"))

    # Jar merge is automatic — turbo picks up the session
    yield scrapy.Request(
        "https://example.com/dashboard",
        meta={"stealth": {"driver": "turbo"}},
    )
```

Opt out of jar merge:

```python
meta = {"stealth": {"driver": "browser", "export_cookies": False}}
```

Stat: `stealth/browser_cookies_exported`

## PUT / PATCH / DELETE

```python
yield scrapy.Request(
    "https://api.example.com/items/1",
    method="PATCH",
    body=b'{"title": "updated"}',
    headers={"Content-Type": "application/json"},
    meta={"stealth": {"driver": "basic"}},
)
```

## Do not set manually

These are stripped and replaced by the active profile:

- `User-Agent`, `Accept`, `Accept-Language`, `Accept-Encoding`
- `sec-ch-ua*`, `sec-fetch-*`, `Upgrade-Insecure-Requests`, etc.

## Driver summary

| Driver    | GET / HEAD                                   | POST / PUT / PATCH / DELETE |
|-----------|----------------------------------------------|-----------------------------|
| `basic`   | Native HTTP + profile TLS                    | Same                        |
| `turbo`   | curl-impersonate TLS                         | Same                        |
| `browser` | Tab navigation; binary URLs return raw bytes | In-page `fetch()`           |
