# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-05-01

### Added

- Dual-driver architecture under `engine="stealth"`: `driver="basic"` (default) and `driver="turbo"` (deeper TLS fingerprinting)
- `TurboEngine` — new stealth engine driver using new techs for impersonation; strips Scrapy fingerprint headers before passing to the driver so its own TLS profile is not overridden
- `config.STEALTH_DRIVER` — global default driver (`"basic"` or `"turbo"`); overridable per-request via `request.meta["driver"]`
- `request.meta["driver"]` — per-request driver override (`"basic"` or `"turbo"`)
- Generic profile resolver in `utils/profiles.py` — `resolve_browser(profile, backend)` returns a basic `Profile` for `"basic"` or a turbo impersonation string for `"turbo"`;
- `response.meta["download_latency"]` — stealth engines automatically inject download latency (formatted as `"1.02s"`) into the response meta,
- `BaseEngine._execute_timed` — internal wrapper that times every `_execute` call and writes `download_latency` into the response meta; all current and future engines inherit this for free
- `StealthResponse._meta` parameter — accepts an optional dict merged into a copy of `request.meta` before building the response, allowing engines to inject stealth-specific keys without mutating the original request
- Python 3.14 support — added `Programming Language :: Python :: 3.14` classifier to `pyproject.toml`
- CI matrix extended with Python 3.14 and OS compatibility jobs for Windows and macOS (Python 3.14 only); all Python versions continue to run on Ubuntu

### Changed

- `engines/basic.py` (renamed from `engines/browser.py`) — `BasicEngine` replaces `BrowserEngine`; imports updated to `utils/profiles.py`
- `utils/profiles.py` (renamed from `utils/browsers.py`) — profile resolution is now backend-aware; both drivers share the same profile name space
- `EngineManager` — updated to instantiate and cache both `BasicEngine` and `TurboEngine`; unknown driver falls back to `BasicEngine`
- `StealthDownloaderMiddleware` — reads `meta["driver"]` and passes it to `EngineManager.get(engine_name, driver)`
- `utils/meta.py` — `"driver"` added to `_STEALTH_ONLY_KEYS` so misuse warnings are emitted when it is set without `engine="stealth"`
- `StealthResponse.encoding` is now dynamic — `TurboEngine` passes `resp.encoding` from response; `BasicEngine` passes `None` so Scrapy auto-detects from headers and body; hardcoded `"utf-8"` fallback removed
- `BaseEngine.fetch` — now delegates to `_execute_timed` instead of `_execute` directly so latency tracking is transparent to all subclasses
- Downloads badge in README switched from `shields.io` to `pepy.tech` to avoid upstream rate-limit errors
- Dependencies: `NL` added to `pyproject.toml`

### Fixed

- `ScrapyEngine` — implemented the `_execute` abstract method (was raising `TypeError: Can't instantiate abstract class ScrapyEngine without an implementation for abstract method '_execute'` at spider startup)

### Tests

- Added 13-test suite for `TurboEngine` covering: response type, HTTP/1.1 and HTTP/2 version selection, fingerprint header stripping, proxy passthrough, body passthrough on POST, turbo profile resolution, exception handling, `TimeoutError` re-raise, and `content-encoding` header removal

---

## [0.2.2] - 2026-04-28

### Added

- HTTP/2 support for the stealth engine — enabled by default (`HTTP2 = True` in `StealthConfig`); disable globally via `config.HTTP2 = False` or per-request via `request.meta["http2"] = False`
- `BasicEngine._get_client` — lazy per-protocol client cache; separate `Client` instances are created for HTTP/1.1 and HTTP/2 on first use

### Changed

- `BasicEngine` — improved stealth client creation log from generic bracket notation to structured `key=value` format: `"Initializing stealth HTTP client (protocol=%s)"`
- `StealthConfig.LOGGER_NAME` — annotated as `Final[str]` to signal immutability; type checkers will flag any attempt to reassign it

---

## [0.2.1] - 2026-04-27

### Fixed

- `BasicEngine.__init__` — `profile` and `timeout` parameters now default to `None` (sentinel) and resolve from `config` at call time, fixing the Python mutable-default anti-pattern that caused runtime `config` changes to be ignored
- `BasicEngine._execute` — removed duplicate `config.get("DEFAULT_PROFILE")` lookup; now uses `self._default_profile` as the single source of truth; `resolve_browser` is skipped when the per-request profile matches the engine default
- `resolve_browser` — removed `None` handling from the function signature (`str | Profile | None` → `str | Profile`); callers are now responsible for resolving defaults before calling, eliminating an implicit config dependency inside the utility

### Changed

- `StealthConfig` test coverage extended to include `BLOCK_CODES`, `BLOCK_KEYWORDS`, `LOGGER_NAME`, `get()` method, and the `config` singleton
- All config-driven values in tests (`DEFAULT_ENGINE`, `DEFAULT_PROFILE`, block codes, etc.) now reference `config.get()` instead of hardcoded strings, so tests stay correct if defaults change
- README: added **Global Configuration** section documenting the `config` singleton, all `StealthConfig` attributes with types and defaults, and `config.get()` usage

---

## [0.2.0] - 2026-04-23

### Added

- Automatic browser profile rotation via `request.meta["rotate_profile"]`
- Automatic proxy rotation via `request.meta["rotate_proxy"]`
- Proxy validation at startup — invalid format or unsupported scheme raises `ValueError` immediately
- Per-spider configuration support via `custom_settings` (middleware and `STEALTH_PROXIES`)
- Warning log when stealth-only meta keys (`profile`, `rotate_profile`, `rotate_proxy`) are used without `engine: stealth`
- Centralised logger via `LOGGER_NAME` constant — all package logs appear under `[scrapy-stealth]`

### Changed

- `STEALTH_PROXIES` is now re-read on `spider_opened` to support per-spider proxy lists
- Internal meta key access centralised in `utils/meta.py` (`_is_meta_enabled`, `_get_meta_data`)
- Rotation logic is skipped when a misuse warning fires, preventing misleading follow-up logs

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

[0.3.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.3.0
[0.2.2]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.2
[0.2.1]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.1
[0.2.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.0
[0.1.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.1.0
