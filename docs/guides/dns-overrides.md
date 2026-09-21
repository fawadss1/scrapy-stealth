# DNS overrides

Pin a hostname to a fixed origin IP. The client connects to that IP while keeping the hostname
for TLS SNI, `Host` header, and certificate verification.

## Global

```python
STEALTH_DNS_OVERRIDES = {
    "shop.example.com": "203.0.113.10",
    "cdn.example.com": "203.0.113.11",
}
```

Or via config:

```python
from scrapy_stealth.config import config

config.STEALTH_DNS_OVERRIDES = {"example.com": "203.0.113.10"}
```

## Per-request

```python
yield scrapy.Request(
    "https://shop.example.com/item/1",
    meta={"stealth": {"driver": "turbo", "dns": "203.0.113.10"}},
)

# Full mapping:
meta = {"stealth": {"dns": {"shop.example.com": "203.0.113.10"}}}
```

## Driver behavior

| Driver | Per-request DNS | Notes |
|--------|-----------------|-------|
| `basic` | Yes | curl resolve list |
| `turbo` | Yes | curl resolve list |
| `browser` | Global at launch | Local CONNECT relay dials pinned IP |

For **browser**, DNS map changes require a browser restart. Do not put DNS-pinned hosts on
`BROWSER_PROXY_BYPASS_LIST` or they skip the relay.

## Proxies

With HTTP proxies, DNS is often resolved by the proxy. Prefer direct connections or SOCKS when
using overrides on `basic`/`turbo`.

## Validation

Invalid IPs raise `ValueError` at startup (settings) or when the request is processed.
