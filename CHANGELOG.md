# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.6.2a2] - 2026-05-19

### Fixed

- **Scrapy 2.12 (Python 3.12) — `RuntimeError: no running event loop` in `BaseEngine.fetch`**
  `asyncio.get_running_loop()` requires the coroutine to be executing inside an asyncio Task.
  In Scrapy 2.12, async downloader middlewares are driven by Twisted's `_inlineCallbacks`
  (via `deferred_from_coro`) rather than an asyncio Task, so `get_running_loop()` raised
  `RuntimeError: no running event loop` on every stealth request.
  `BaseEngine.fetch` now falls back to `asyncio.get_event_loop()` when `get_running_loop()`
  raises `RuntimeError`, which safely retrieves the Twisted asyncio reactor's event loop in
  that context while still using the true running loop on Scrapy 2.15+.

---

## [0.6.2a1] - 2026-05-19

### Fixed

- **Zyte (ScrapyCloud) — `FileException: download-error` on `scrapy:2.15` stack**
  `BaseEngine.fetch()` used Twisted's `deferToThread` to dispatch blocking HTTP calls to a thread pool.
  In Scrapy 2.15 on Python 3.14 the media pipeline's new fully-async architecture calls
  `crawler.engine.download_async()` and relies on native asyncio awaiting; the Twisted→asyncio
  bridge (`deferred_to_future` / `ensure_awaitable`) no longer reliably resolved these Deferreds,
  causing file/image downloads to fail before `media_downloaded` received a valid response, which
  then raised `FileException("download-error")`.
  `BaseEngine.fetch()` is now `async def` and uses `asyncio.get_running_loop().run_in_executor()`
  — semantically identical (blocking I/O runs in a thread pool) but returns a native coroutine
  that Scrapy 2.15 can properly await.
  `ScrapyEngine.fetch()` and `StealthDownloaderMiddleware.process_request()` are also made `async`
  for consistency. Twisted imports removed from both files.

- **Zyte (ScrapyCloud) — `ImportError: cannot import name 'request_fingerprint'` on `scrapy:2.11` stack**
  `scrapy-stealth` previously declared `scrapy>=2.15.2` as a hard dependency.
  Installing the package on a `scrapy:2.11` Zyte stack caused pip to upgrade Scrapy to 2.15.2+,
  which removed `request_fingerprint` from `scrapy.utils.request`.
  Zyte's bundled `sh_scrapy` extension still imports that symbol, so the spider process crashed
  before the first request.
  The Scrapy lower-bound is now `>=2.12.0,<3.0`; `scrapy-stealth` uses no Scrapy 2.15-specific
  APIs, so the relaxed constraint is safe and prevents the forced upgrade.

---

## [0.6.1] - 2026-05-18

### Fixed

- **Zyte (ScrapyCloud) — `ValueError: invalid literal for int()` on `download_latency`**
  `BaseEngine._execute_timed` stored download latency as a formatted string (`"0.18s"`) instead of a numeric value. Zyte's `sh_scrapy` pipe writer calls `int(duration)` and expects a plain number; the string caused a `ValueError` at response write time, and the string was repeated across concurrent/retried requests making it unreadable.
  `download_latency` is now stored as a plain `float` (e.g. `0.18`), consistent with Scrapy's own HTTP downloader.

### Added

- **`utils/meta_info.py` — `PackageMetadata` utility**
  Frozen dataclass that reads `name`, `version`, `author`, `email`, `license`, `summary`, and `homepage` from the installed distribution metadata via `importlib.metadata`.
  Parses `"Name <email>"` author strings with a regex, picks the first available URL field, and falls back to compile-time defaults when the package is not installed (e.g. running from source without `pip install -e .`).
  A module-level singleton `_pkg_meta` is resolved once at import time; `__init__.py` now derives `__version__`, `__author__`, and `__license__` from it. `PackageMetadata` is exported in `__all__`.

---

## [0.6.0] - 2026-05-12

### Fixed

- **Browser engine — `StopIteration` / `RuntimeError` crash under concurrent load**
  `browser.get(url)` without `new_tab=True` reused the persistent main tab; after `page.close()` the main tab was destroyed, so the next call to `browser.get()` found no `"page"` targets and raised `StopIteration` inside a coroutine (→ `RuntimeError: coroutine raised StopIteration`).
  All fetches now use `browser.get(url, new_tab=True)` — each request gets its own isolated tab, the main tab stays alive permanently, and `StopIteration` can never occur.

- **Browser engine — noisy `[asyncio] ERROR: Task exception was never retrieved` spam**
  nodriver fires background `update_targets()` tasks on a timer; when Chrome restarts these tasks raise `ConnectionRefusedError` which asyncio logs as unhandled task exceptions.
  A custom loop exception handler now suppresses `ConnectionRefusedError` from the browser event loop, eliminating the log noise.

- **Browser engine — automatic crash recovery**
  On `ConnectionRefusedError` (Chrome process died) the engine now restarts the browser and retries the current request once before giving up.
  A dead-browser guard (`dead_browser` parameter on `_reset_browser`) prevents multiple concurrent threads from each triggering a redundant restart.

### Added

- **`BROWSER_MAX_TABS`** (default `10`) — caps the number of Chrome tabs open simultaneously via an asyncio `Semaphore`, preventing Chrome from being overwhelmed when Scrapy fires many concurrent requests.
  Configurable via `config.BROWSER_MAX_TABS` or `constants.BROWSER_MAX_TABS`.

- **`BROWSER_RESTART_EVERY`** (default `200`) — proactively restarts Chrome every N requests to prevent memory bloat on long high-volume runs.
  Configurable via `config.BROWSER_RESTART_EVERY` or `constants.BROWSER_RESTART_EVERY`.

- **`utils/session.py` — `SessionCache[K, V]`** — generic lazy per-thread cache backed by a factory callable.
  Each Twisted thread pool thread maintains its own isolated dict; the factory is called once per key per thread and the result is reused on every subsequent call from that thread.
  Eliminates the boilerplate `threading.local()` + `hasattr` + dict pattern that both `BasicEngine` and `TurboEngine` previously duplicated.

### Changed

- **`TurboEngine` — persistent thread-local sessions** (performance)
  Previously a fresh `Session` was created and destroyed for every request, incurring a full TLS handshake cost each time.
  Sessions are now cached per `(thread, impersonation-profile)` via `SessionCache`, enabling TCP connection reuse and TLS session resumption within each Twisted thread pool thread.

- **`BasicEngine` — thread-local clients** (correctness + performance)
  The previous `self._clients: dict[bool, Client]` was shared across all Scrapy threads, creating a potential concurrent-write race on first use and preventing per-thread connection pooling.
  Replaced with `SessionCache` — each thread gets its own `wreq.Client` per http2 setting.

- **`BROWSER_MAX_TABS` and `BROWSER_RESTART_EVERY`** added to `constants.py` and registered as `StealthConfig` attributes so they are accessible via `config.get()` like all other browser settings.

---

## [0.5.0] - 2026-05-11

### Added

#### Real Browser Engine (`driver="browser"`)

A third stealth driver powered by a real Chrome instance via the Chrome DevTools Protocol (no WebDriver).
Designed for Cloudflare-protected pages, heavy JavaScript SPAs, and any site that defeats HTTP-level impersonation.

Key characteristics:
- **No WebDriver** — communicates over CDP directly; `navigator.webdriver` is never set
- **Persistent browser, tab-per-request** — one Chrome process is reused across requests; each request opens a new tab and closes it when done, keeping memory overhead low
- **Proxy isolation** — when a proxy is set, a fresh browser is started per request so every request exits from a different IP with no shared state
- **Splash screen** — loads the project logo before the target URL when using a proxy, warming up the browser context
- **Configurable globally** via `config.BROWSER_HEADLESS` (default `True`) and `config.BROWSER_SETTLE_S` (default `4.0`)
- **Per-request overrides** via `meta["stealth"]["headless"]` and `meta["stealth"]["settle"]`

#### Browser Snapshots

Capture a full-page PNG of any browser-rendered page and access the raw bytes in the response:

#### `@snapshot` Decorator (`scrapy_stealth.decorators`)

New `decorators` package with a `snapshot` decorator that auto-saves the PNG to disk before the callback.

- Creates intermediate directories automatically
- Auto-generates a timestamped filename when `path` is omitted
- Logs an error (does not raise) if `snapshot=True` was not set on the request
- Raises `TypeError` if called directly as a method instead of used as a decorator
- Middleware logs an error if `snapshot=True` is used with a non-browser driver

---

## [0.4.0] - 2026-05-06

### Changed

- **Breaking:** All per-request stealth options are now namespaced under `request.meta["stealth"]` instead of flat `request.meta` keys.
  This mirrors the pattern used by other scrapy-contributors and prevents key collisions with other middleware.
  The presence of the `stealth` key activates the stealth engine — no `"engine"` key needed.

  ```python
  # Before
  meta={"engine": "stealth", "rotate_profile": True, "proxy": "http://..."}

  # After
  meta={"stealth": {"rotate_profile": True, "proxy": "http://..."}}
  ```

  Affected keys: `driver`, `profile`, `proxy`, `stealth_timeout`, `http2`, `rotate_proxy`, `rotate_profile`.
  The `engine` per-request key has been removed — engine selection is now implicit from the presence of `meta["stealth"]`.

- `RetryHandler.build` — retry request now sets `meta["stealth"]` (empty dict if not already present) to activate the stealth engine
- `utils/meta.py` — `_get_meta_data` and `_is_meta_enabled` read from `request.meta.get("stealth", {})`;
  `_stealth_ignored_warn` and `_STEALTH_ONLY_KEYS` removed (no longer needed);
  `STEALTH_KEY = "stealth"` exported as the canonical namespace key

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

[0.6.1]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.1
[0.6.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.0
[0.5.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.5.0
[0.4.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.4.0
[0.3.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.3.0
[0.2.2]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.2
[0.2.1]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.1
[0.2.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.0
[0.1.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.1.0
