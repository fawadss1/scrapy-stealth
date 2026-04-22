# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-04-22

### Added

- Browser impersonation with 70+ profiles across Chrome, Firefox, Safari, Edge, Opera, and mobile browsers
- Realistic per-profile HTTP headers matched to each browser family
- Proxy rotation via `ProxyRotator`
- Browser fingerprint rotation via `ProfileRotator` with weighted selection favouring newer browsers
- Blocked response detection and automatic retry via `RetryHandler`
- Anti-bot detection via `AntiBotDetector` (status codes + page content keywords)
- Per-request engine selection via `request.meta["engine"]`
- `StealthConfig` for centralised configuration defaults

---

[0.1.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.1.0
