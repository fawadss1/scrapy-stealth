# Scrapy stats

scrapy-stealth records telemetry on `crawler.stats`. Inspect after the crawl or in
`spider_closed`:

```python
def closed(self, reason):
    stats = self.crawler.stats.get_stats()
    self.logger.info(
        "bans=%s recycles=%s proxy_failures=%s",
        stats.get("stealth/bans"),
        stats.get("stealth/recycles"),
        stats.get("stealth/proxy/connection_failures"),
    )
```

## Request / response

| Key                                                | Meaning                     |
|----------------------------------------------------|-----------------------------|
| `stealth/requests` / `stealth/requests/{driver}`   | Stealth fetches             |
| `stealth/responses` / `stealth/responses/{driver}` | Completed responses         |
| `stealth/successes` / `stealth/successes/{driver}` | Non-banned, status &lt; 400 |
| `stealth/failures` / `stealth/failures/{driver}`   | Banned or status ≥ 400      |
| `stealth/status/{code}`                            | Count by HTTP status        |

## Bans & recycle

| Key                                              | Meaning                        |
|--------------------------------------------------|--------------------------------|
| `stealth/bans` / `stealth/bans/{driver}`         | Session-ban responses          |
| `stealth/ban_streak`                             | Current consecutive ban streak |
| `stealth/recycles` / `stealth/recycles/{driver}` | Session / Chrome recycles      |

## Identity

| Key               | Meaning                                    |
|-------------------|--------------------------------------------|
| `stealth/driver`  | Last driver used                           |
| `stealth/profile` | Last fingerprint profile                   |
| `stealth/proxy`   | Last proxy as `host:port` (no credentials) |

## Proxy health

| Key                                                | Meaning                   |
|----------------------------------------------------|---------------------------|
| `stealth/proxy/requests` / `…/{driver}`            | Requests through a proxy  |
| `stealth/proxy/connection_failures` / `…/{driver}` | Transport failures        |
| `stealth/proxy/last_connection_failure`            | Host of last dead proxy   |
| `stealth/proxy/cooldowns` / `…/{driver}`           | Proxy cooldown events     |
| `stealth/proxy/last_cooldown`                      | Host of last cooled proxy |
| `stealth/proxy/rotations` / `…/{driver}`           | Rotations after failure   |

## DNS, fallback, cookies, throttle

| Key                                                | Meaning                        |
|----------------------------------------------------|--------------------------------|
| `stealth/dns/requests/{driver}`                    | Requests with DNS overrides    |
| `stealth/dns/hosts`                                | Total pinned hosts applied     |
| `stealth/fallbacks` / `stealth/fallbacks/{driver}` | `auto` → browser escalations   |
| `stealth/fallbacks/method/{method}`                | Fallbacks by HTTP method       |
| `stealth/browser_cookies_exported`                 | Cookies merged into Scrapy jar |
| `stealth/throttle/waits`                           | Throttle wait events           |
| `stealth/throttle/wait_ms`                         | Total throttle wait time       |
| `stealth/throttle/rate_limited`                    | 429-driven throttles           |
| `stealth/throttle/retry_after`                     | Retry-After honored            |
