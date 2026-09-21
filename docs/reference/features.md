# Features

## Core

- Pluggable engine system (`scrapy`, stealth drivers)
- Per-request engine selection via `request.meta["stealth"]`
- Native Scrapy middleware integration (thread-safe async)

## Stealth & evasion

- **Browser-level impersonation** — TLS + HTTP/2 fingerprints (`turbo`, `basic`)
- **Real Chrome via CDP** — JS-heavy pages, Cloudflare, login flows (`browser`)
- **Smart `auto` fallback** — HTTP first, browser on challenge or ban
- **Behavioral fingerprinting** — CDP mouse/scroll/viewport on browser; timing jitter on HTTP drivers (auto-enabled)
- **Adaptive rate limiting** — per-domain AIMD throttle on 429 / `Retry-After` (auto-enabled)
- **Anti-bot detection** — status + content patterns (Cloudflare, Akamai, DataDome, …)

## Proxies & networking

- **Smart Proxy Management** — per-domain health, cooldown, failover, stats telemetry
- Built-in proxy rotation from `STEALTH_PROXIES`
- **Custom DNS overrides** — pin hosts to fixed IPs (TLS/SNI/Host unchanged)
- Proxy bypass list for browser (`BROWSER_PROXY_BYPASS_LIST`)
- HTTP/3 (QUIC) on turbo when enabled

## Sessions & reliability

- Intelligent session recycle after consecutive bans (Chrome restart or HTTP client clear)
- Smart retry strategies (`RetryHandler`)
- Fingerprint rotation from weighted profile pool
- Static asset blocking in browser (optional, skipped for snapshots)

## Requests & cookies

- Full request fidelity — POST/PUT/PATCH/DELETE, custom headers, cookies on all drivers
- Browser cookie handoff — tab cookies exported to response meta and Scrapy jar
- Cloudflare challenge wait on browser driver (`BROWSER_CHALLENGE_TIMEOUT_S`)
- CDN/binary URLs — raw bytes for `.jpg`, `.png`, etc. when served directly

## Observability

- Rich Scrapy stats (`stealth/*` keys) — bans, recycles, proxy health, fallbacks, throttle
- Optional styled console logs (`STEALTH_LOGS`)
- Built-in snapshot decorator for browser PNG captures

## See also

- [Drivers overview](../drivers/overview.md)
- [Global settings](../configuration/settings.md)
- [Scrapy stats](stats.md)
