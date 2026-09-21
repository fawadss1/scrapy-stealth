# Smart Proxy Management

When using `STEALTH_PROXIES` or `meta["stealth"]["proxy"]`, scrapy-stealth tracks health **per proxy and per target domain**.

Dead credentials, tunnel errors (407, CONNECT aborted), and repeated blocks automatically cool down bad entries and rotate to the next
proxy in the pool.

## Signals

| Signal                                          | Action                                             |
|-------------------------------------------------|----------------------------------------------------|
| Transport failure (407, CONNECT, DNS via proxy) | Record failure → rotate → cooldown after threshold |
| Repeated HTTP blocks (403 by default)           | Same cooldown via `STEALTH_PROXY_CIRCUIT_CODES`    |
| Ban-streak session recycle                      | Profile + proxy rotate together                    |

## Settings

```python
STEALTH_PROXIES = [
    "http://user-a:pass@proxy.example.com:8000",
    "http://user-b:pass@proxy.example.com:8000",
]
STEALTH_PROXY_HEALTH = True  # default
STEALTH_PROXY_CIRCUIT_AFTER = 3
STEALTH_PROXY_COOLDOWN_S = 300.0
STEALTH_PROXY_CIRCUIT_CODES = {403}
```

Supported schemes: `http`, `https`, `socks4`, `socks5`.

## Per-request

```python
yield scrapy.Request(
    url,
    meta={"stealth": {"proxy": "http://user:pass@proxy.example.com:8080"}},
)

# Direct — no proxy for this URL
yield scrapy.Request(cdn_url, meta={"stealth": {"proxy": None}})
```

## Stats

See [Scrapy stats](../reference/stats.md):

- `stealth/proxy/connection_failures`
- `stealth/proxy/cooldowns`
- `stealth/proxy/rotations`
- `stealth/proxy/last_connection_failure`

## Browser proxy bypass

Send specific domains direct to origin (not through proxy):

```python
BROWSER_PROXY_BYPASS_LIST = ["example.com", "*.internal.net", "<local>"]
```

Global Chrome launch flag — only applies when a proxy is in use.
