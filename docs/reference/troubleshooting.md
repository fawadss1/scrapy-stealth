# Troubleshooting

## Cookies not applied / wrong currency or locale

1. Pass cookies on **every** `Request`, not only the first URL
2. Use `Request(cookies={...})` or `headers={"Cookie": "..."}` — both work with stealth
3. Keep `COOKIES_ENABLED = True`
4. Put `STEALTH_LOGS` in **settings**, not `request.meta`
5. Some sites reject **stale** cookie values (e.g. old `user-settings` timestamps) — refresh
   from the browser or generate a fresh timestamp

## `STEALTH_LOGS` has no effect

Must be in `settings.py` or spider `custom_settings`:

```python
custom_settings = {"STEALTH_LOGS": False}
```

Not in `request.meta`.

## Browser not found

Install Chrome/Chromium or set:

```python
BROWSER_EXECUTABLE_PATH = "/path/to/chrome"
```

On Windows, install [VC++ redistributables](../getting-started/installation.md) if `wreq`
(basic driver) fails to import.

## Turbo connection failed

- Verify proxy allows HTTPS to the target host
- Try `meta={"stealth": {"http2": False}}`
- Try `driver="basic"` to isolate curl_cffi vs wreq
- Test without proxy first

## Always getting 403

Often **IP/proxy reputation**, not fingerprint:

- Try residential/mobile proxy
- Use `driver="auto"` for JS challenges
- Check `stealth/bans` and `stealth/proxy/cooldowns` stats
- Browser + bad IP still returns 403 on DataDome/CDN blocks

## Browser slow

Expected (~5–15 s/page). Use `driver="auto"` or `turbo` for bulk crawling; reserve `browser`
for login/challenge URLs only.

## DNS override not working (browser)

Browser DNS is applied at **launch** via a local relay. Changing overrides mid-crawl restarts
Chrome. Do not add pinned hosts to `BROWSER_PROXY_BYPASS_LIST`.

## Docker / root

```python
BROWSER_NO_SANDBOX = True
BROWSER_EXECUTABLE_PATH = "/usr/bin/chromium"
```

## Local checks before push

```bash
pip install -e ".[dev]"
python scripts/check.py
```

See [Contributing](../development/contributing.md).
