# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

---

## [Unreleased]

### Added

* **Proxy-Seller sponsor**
  README and `AGENTS.md` now include Proxy-Seller with affiliate link, promo code `FAWAD15`, and logo assets under `docs/static/sponsors/`.

---

## [0.6.15] - 2026-08-18

### Added

* **POST / PUT / PATCH / DELETE on all drivers**
  `basic`, `turbo`, and `browser` honor the same Scrapy `Request` fields — method,
  body, `Cookie`, and custom headers (`Content-Type`, `Authorization`, etc.).

* **Single request builder for all drivers**
  `build_stealth_request()` in `scrapy_stealth.utils.network.request` validates
  and normalizes method, URL, body, `Cookie`, and custom headers once. Browser
  POST uses in-page `fetch()` via `browser_http_fetch()`.

* **README and example spider**
  New “POST, headers, and cookies” section with live test URLs
  (`postman-echo.com`, `quotes.toscrape.com`, `jsonplaceholder.typicode.com`).
  `examples/full_spider.py` demonstrates JSON POST on all three drivers and form
  login via browser.

### Fixed

* **Browser POST — same-origin setup**
  Load the target URL (GET), not the site root, before in-page `fetch()`. Fixes
  `TypeError: Failed to fetch` when the root redirects elsewhere
  (e.g. `postman-echo.com` → `www.postman.com`).

* **Browser POST — brotli decode error in Scrapy**
  Strip `content-encoding` and `content-length` from browser fetch responses; the
  body from `arrayBuffer()` is already decoded.

* **Basic driver — POST body dropped**
  wreq expects raw bytes as `body=`, not `data=` (turbo/curl_cffi uses `data=`).
  Added `StealthRequestPayload.basic_http_kwargs()` for the basic engine.

* **Browser CDP headers on POST setup**
  Do not send `Content-Type` / `Content-Length` via CDP extra headers during
  origin setup; they are set only on the in-page `fetch()` call.

### Changed

* Browser POST context verifies same-origin after navigation and checks for Chrome
  error pages before running `fetch()`.

---

## [0.6.14] - 2026-08-17

### Changed

* **PyPI wheel/sdist packaging**
  Ship only `scrapy_stealth` and `docs/static/logo.png` (browser splash). Exclude
  `examples/`, `scripts/`, sponsor assets, and other docs from installs.

* **`STEALTH_ENABLED` uses smart driver selection by default**
  When global stealth is on, the middleware injects `meta["stealth"]["driver"] = "auto"`
  on requests that do not already specify a driver. HTTP impersonation (`turbo` by default,
  or `STEALTH_DRIVER`) runs first; JS challenges and session bans retry once with the
  `browser` driver.

* **`STEALTH_DRIVER` default is now `"turbo"`**
  `driver="auto"` and global stealth now start with the turbo driver for stronger TLS
  impersonation. Set `STEALTH_DRIVER = "basic"` for the lighter HTTP driver.

### Removed

* **`STEALTH_AUTO_FALLBACK` setting**
  Browser fallback is controlled solely by `driver="auto"` (injected automatically when
  `STEALTH_ENABLED = True`, or set per-request). Use `meta["stealth"]["fallback"] = False`
  to opt out for a single URL.

### Fixed

* **Browser splash logo showed a blank tab on startup**
  `_splash_url()` loads `docs/static/logo.png` (included in PyPI wheels for splash).

---

## [0.6.13] - 2026-08-13

### Changed

* **NodeMaven sponsor materials**
  Updated README and `AGENTS.md` with new copy, tracking links (`Fawadss1readmegh`, `Fawadss1agentmdgh`, `Fawadss1tools`), and the new horizontal banner (`docs/static/sponsors/nodemaven-banner.png`).

* **Utils package layout**
  Reorganised `scrapy_stealth.utils` into subpackages: `core`, `detection`,
  `network`, `browser`, `engine`, and `telemetry`. Import paths updated
  (e.g. `scrapy_stealth.utils.core.meta`, `scrapy_stealth.utils.network.proxy`).

---

## [0.6.12] - 2026-08-10

### Changed

* **Middleware — drop deprecated `spider` arg from `process_request`**
  Matches current Scrapy downloader middleware API: the spider is read from the
  crawler saved in `from_crawler()` (`crawler.spider`) instead of a method
  argument. Removes the `ScrapyDeprecationWarning` about
  `StealthDownloaderMiddleware.process_request()`.

### Added

* **Smart browser selection (`STEALTH_AUTO_FALLBACK`, `driver="auto"`)**
  When `basic` or `turbo` returns a JS challenge or session ban, the middleware
  retries once with the `browser` driver. The fallback always runs with
  `headless=False` for better evasion. Opt in globally with
  `STEALTH_AUTO_FALLBACK = True`, per-request with
  `meta["stealth"]["driver"] = "auto"`, or opt out with
  `meta["stealth"]["fallback"] = False`. Fallback counters appear under
  `stealth/fallbacks` in `crawler.stats`.

---

## [0.6.11] - 2026-08-04

### Added

* **Scrapy stealth stats**
  Request, response, success, failure, status, ban, recycle, proxy-use, and DNS-use
  counters appear in `crawler.stats`, globally and by driver where useful. Current
  driver, profile, redacted proxy, ban streak, and active DNS host count are also
  exposed. Collection reuses existing response / ban checks: no extra body parsing,
  network requests, or per-domain high-cardinality stats.

* **Middleware closes engines on `spider_closed`**
  Chrome, the DNS CONNECT relay, and the browser asyncio loop are torn down when
  the spider finishes instead of lingering until process exit.

* **Full spider example**
  [`examples/full_spider.py`](examples/full_spider.py) demonstrates settings,
  per-request drivers, snapshots, ban detection, and stealth stats. README links
  to it instead of embedding a long copy.

### Changed

* **Faster browser shutdown**
  `BrowserEngine.close()` / recycle stop Chrome before draining asyncio tasks, use
  shorter teardown timeouts, and delete nodriver temp data (profiles, caches,
  cookies, GPU/shader data, and logs) on a background thread via
  `_cleanup_browser_temp_data()`.

---

## [0.6.11a1] - 2026-07-27

### Added

* **Basic / turbo — session recycle after consecutive bans**
  `STEALTH_RECYCLE_AFTER_BANS` (and `STEALTH_RECYCLE_COOLDOWN_S`) apply to `basic` and
  `turbo`: after N consecutive banned responses, cached HTTP clients/sessions are cleared and
  the engine default fingerprint profile **and** proxy (from `STEALTH_PROXIES`) are rotated.
  Same ban heuristics as the browser engine (`is_browser_session_ban`). Explicit meta
  `profile` / `proxy` still win. `BanStreakTracker` lives in `utils/session.py`.

* **`STEALTH_PROXIES` on config**
  Proxy pool is loaded from Scrapy settings into `config.STEALTH_PROXIES` and seeded as the
  engine default; rotated on ban-streak recycle.

### Changed

* **Renamed recycle settings**
  `BROWSER_RESTART_AFTER_BANS` → `STEALTH_RECYCLE_AFTER_BANS`,
  `BROWSER_RESTART_COOLDOWN_S` → `STEALTH_RECYCLE_COOLDOWN_S` (apply to all drivers).

* **Removed `rotate_profile` / `rotate_proxy` meta flags**
  Profile and proxy now change automatically on ban-streak session recycle only.
  Set `STEALTH_PROXIES` in settings; use explicit `meta["stealth"]["profile"]` /
  `["proxy"]` when you need a fixed identity.

### Fixed

* **Meta-only proxy cleared to `None` on recycle**
  When `STEALTH_PROXIES` is empty, recycle keeps the request's `meta["stealth"]["proxy"]`
  instead of wiping the engine default.

* **Concurrent recycle storm / stuck-together console lines**
  `BanStreakTracker` claims only once per ban wave so parallel Scrapy threads do not all
  recycle and print at once. Console output is lock-protected with `flush=True`.

---

## [0.6.10] - 2026-07-23

### Added

* **Custom DNS overrides (`STEALTH_DNS_OVERRIDES` / `meta["stealth"]["dns"]`)**
  Pin hostnames to fixed origin IPs so `basic` / `turbo` connect via that address while keeping the hostname for TLS SNI, Host header, and certificate verification. Configure globally via Scrapy settings / `config.STEALTH_DNS_OVERRIDES`, or per-request with a bare IP (`"dns": "203.0.113.10"`) or a `{host: ip}` map. The `browser` driver applies the effective map via a local CONNECT relay that dials the pinned IP (not Chrome `--host-resolver-rules`). Invalid IPs raise `ValueError` at startup / resolve time.

### Changed

* **Dependency: Required for the `DnsOptions` API used by custom DNS overrides (`ResolverOptions`).

* **Basic engine DNS — apply `dns_options` on `Client(...)`**
  wreq ignores per-request `dns_options=` on `get()`/`post()`; clients are now cached per `(http2, dns map)` like turbo sessions.

* **Browser engine DNS — local CONNECT relay**
  Replaced unreliable `--host-resolver-rules` with a DNS-aware local proxy relay (same mechanism as proxy auth injection). Pinned hosts are dialed by IP while Chrome keeps the original hostname for TLS.

* **Browser relay — silence shutdown races / dial IPs without getaddrinfo**
  Pinned-IP connects use `sock_connect` so Windows Proactor no longer hits `RuntimeError: cannot schedule new futures after shutdown` when Chrome still CONNECT-retries during browser restart. Loop/executor teardown errors in the relay callback are swallowed.

* **Browser engine — blank tab / wait / relay consistency**
  Disabled `enable_begin_frame_control` on tab create. Browser always uses the local CONNECT relay (even with no DNS/proxy). Replaced nodriver `page.wait()` with `_wait_for_document`. `_wait_for_status` returns ~0.75s after document complete when Navigation Timing never fills. `_smart_wait` long-poll only for short challenge/script-only shells. Challenge HTML heuristics no longer match bare `akamai` / `captcha` / `please wait.` / `enable javascript` / `datadome` / `kasada`.

* **Browser engine — close tab as soon as `_smart_wait` passes**
  `_smart_wait` returns immediately when body content is ready (`settle` is a max wait for growth, not a sleep after ready). HTML is captured, the fetch tab is closed via CDP, then the response is returned. Chrome is stopped when idle so the window is not left on `about:blank`.

* **Browser splash — show `docs/static/logo.png`**
  `_splash_url()` loads the package logo via `file://` when the file exists (falls back to `about:blank`).

---

## [0.6.10a2] - 2026-07-03

### Added

* **Automatic PyPI update check**
  When `StealthDownloaderMiddleware` is loaded, scrapy-stealth checks PyPI once per process in a background thread. If a newer version is published, an info message is printed with `pip install -U scrapy-stealth` and a link to that release on PyPI (e.g. `https://pypi.org/project/scrapy-stealth/0.7.0/`). Network errors are silent and never interrupt crawling.

* **Local CI helper (`scripts/check.py`, `CHECK.md`)**
  Run the same ruff, format, mypy, and pytest checks as GitHub Actions locally before pushing.

* **`is_browser_session_ban()` — stricter ban detection for browser restarts**
  New helper in `utils/antibot.py`. HTTP block codes (403, 429, 503) always count; keyword and JS-challenge heuristics apply only to short pages (< 2500 bytes). Large HTTP 200 documents that embed anti-bot scripts (e.g. DataDome on RS Online) are no longer treated as bans.

### Changed

* **`.gitignore`** — ignore `stealth_snapshots/`, the default output directory for browser snapshots saved via the `@snapshot` decorator.

* **`BROWSER_RESTART_COOLDOWN_S`** — default reduced from `60` to `15` seconds and reworked. Cooldown now spaces ban-triggered restarts when every concurrent request keeps returning 403, without blocking the first restart or all subsequent restarts for a full minute. Configurable via `config.BROWSER_RESTART_COOLDOWN_S`.

* **`BanStreakTracker`** — restart is signalled once per ban wave (`_restart_due` flag); bans during an active restart (`_restarting=True`) are ignored; streak resets when restart begins (`acknowledge_restart()` before `_reset_browser()`).

### Fixed

* **Browser engine — false “5 consecutive bans” restarts on HTTP 200**
  `_maybe_restart` now uses `is_browser_session_ban()` instead of generic `is_blocked()` + `is_js_challenge()`, which matched anti-bot script fragments in otherwise valid product pages.

* **Browser engine — only one restart after 5 bans, then never again**
  Removed the broken 60s cooldown that treated `_last_restart = 0` as “just restarted” and blocked the first restart; later removed the all-or-nothing cooldown that prevented any second restart within 60s.

* **Browser engine — restart storm every 1–2 seconds under concurrent 403s**
  Fixed duplicate restart signals when streak exceeded the threshold, bans piling up during Chrome reset, and concurrent threads all triggering `_reset_browser()` in the same ban wave.

* **Browser engine — `CancelledError` and empty “request failed” logs during restart**
  Fetches cancelled mid-restart now wait for Chrome to come back (`_wait_for_browser_ready()`) and retry up to 5 times. Fixed a deadlock from calling `_wait_for_browser_ready()` while already holding the engine lock.

* **Browser engine — intermittent empty HTML on JS-heavy pages (HTTP 200)**
  `_smart_wait` no longer skips the settle delay when the body text is already long.

---

## [0.6.10a1] - 2026-07-01

### Added

* **Browser restart cooldown (`BROWSER_RESTART_COOLDOWN_S`)**
  Minimum seconds between browser restarts (default `60`). Prevents restart storms when many concurrent tabs all receive 403s from the same blocked session.

### Fixed

* **Browser engine — restart not firing after 5 consecutive bans**
  `BanStreakTracker.record()` no longer resets the streak or starts the cooldown until the restart actually completes (`acknowledge_restart()`). Previously, a restart signal could be consumed while another restart was already in progress (`_restarting=True`), leaving Chrome running with a false cooldown active.

* **Browser engine — `Browser engine timed out after 30s` under load**
  The browser fetch deadline now includes settle time and headroom for status polling and tab-queue wait (`stealth_timeout + settle + 12`).

* **Windows — `ValueError: I/O operation on closed pipe` on browser restart**
  Suppressed benign asyncio subprocess teardown noise via `sys.unraisablehook`; added a short post-join pause in `_stop_loop` on Windows.

* **Engine errors — backend library tracebacks hidden**
  and other backend failures are now re-raised as `StealthTimeoutError` / `StealthConnectionError` via `raise_stealth()` (`from None`), so Scrapy logs show only scrapy-stealth exception frames.

---

## [0.6.9] - 2026-06-29

### Added

* **Proxy bypass list (`BROWSER_PROXY_BYPASS_LIST`)**
  Route chosen domains around the proxy in the browser engine. The user-supplied list is passed to Chrome's `--proxy-bypass-list`
  launch flag, so requests to those domains connect to the origin directly instead of through the proxy relay. Supports the full Chrome
  bypass syntax — bare hostnames, wildcards (`*.example.com`), IP/CIDR ranges, ports, and the `<local>` token. Configured globally via
  config/settings; only takes effect when a proxy is in use.

### Fixed

* **Browser engine — pending tasks destroyed on ban-triggered restart**
  When one Scrapy thread triggered a browser restart after consecutive bans,
  other concurrent `_run_fetch` coroutines and their `_smart_wait` ``sleep()``
  children were left running on the old event loop and destroyed during
  teardown. Restarts now block new fetches behind a restart barrier, drain
  **all** pending loop tasks before stopping Chrome, and retry transient
  connection errors once on the fresh browser.

* **Browser engine — wrong-tab / `cannot call get() concurrently`**
  Replaced `browser.get(url, new_tab=True)` with direct `cdp.target.create_target(url)` to
  guarantee a 1:1 mapping between the created CDP target and the Tab object, eliminating the
  wrong-tab race and the duplicate `_listener_task` that caused the concurrency assertion.

* **Browser engine — `_do_fetch` tasks leaked on timeout**
  Tasks continued running after `future.result(timeout=...)` raised `TimeoutError`, holding
  `_tab_sem` slots and producing "Task was destroyed but it is pending!" on teardown.
  The task is now cancelled directly via `loop.call_soon_threadsafe(task.cancel)` on timeout.

* **Browser engine — `"Event loop is closed"` log noise**
  `_chain_future` callbacks and `call_soon_threadsafe` handles firing against a closed loop
  after `_reset_browser` are now suppressed by a teardown filter on the `asyncio` and
  `concurrent.futures` loggers.

* **Browser engine — `AttributeError: 'NoneType' object has no attribute 'get'`**
  Snapshotting `browser = self._browser` at `_do_fetch` entry prevents `_reset_browser`
  nulling `self._browser` mid-execution from reaching `browser.get()`.

* **Browser engine — Akamai 403 consuming full 30 s timeout**
  `_wait_for_status` now fast-exits on error page titles (Access Denied, Forbidden, etc.)
  returning 403 immediately. `_smart_wait` exits early when body length stops growing for 3 s.

* **Browser engine — `logo.png` splash causing wrong-tab on startup**
  `_splash_url()` now returns `"about:blank"` instead of a `file://` URI.

* **Proxy relay — orphaned `handle()` tasks on restart / shutdown**
  `ProxyRelay.await_closed()` now cancels and awaits all live `handle()` tasks before
  closing the server, replacing the bare `server.close()` that left tasks running.

* **Windows Proactor — `InvalidStateError` crashing the browser loop thread**
  `_run_loop` wraps `loop.run_forever()` in `try/except asyncio.InvalidStateError`;
  the loop exception handler suppresses it as well.

* **Windows browser-restart log noise (`WinError 995`)**
  Suppressed benign Windows Proactor teardown errors logged when the event loop and proxy relay are torn down during a browser restart.
  The loop exception handler now ignores `WinError 995` (`ERROR_OPERATION_ABORTED`) and `WinError 64` (`ERROR_NETNAME_DELETED`)
  alongside the existing `10054` (`WSAECONNRESET`); genuine errors are still surfaced. The restart itself was always succeeding — only
  the spurious `ERROR` tracebacks are gone.

* **Temp browser data — `uc_*` dirs accumulating in `%TEMP%`**
  `_cleanup_browser_temp_data()` removes complete stale nodriver data dirs on every restart and shutdown.

### Changed

* **Console** — timestamp now styled `Fore.YELLOW` to match Scrapy's log format.

---

## [0.6.8] - 2026-06-18

### Added

* **Intelligent content wait (`_smart_wait`)**
  Automatically detects JavaScript challenges, CAPTCHAs, and anti-bot interstitial pages and waits for meaningful page content before
  returning a response, improving success rates on protected websites.
* **Advanced challenge detection**
  Added comprehensive detection for Cloudflare, DataDome, Akamai, Kasada, and other common anti-bot challenge pages.
* **Randomized browser fingerprinting**
  Browser sessions now launch with realistic randomized window sizes and language configurations to reduce fingerprint consistency
  across sessions.
* **Intelligent browser restart (`BROWSER_RESTART_AFTER_BANS`)**
  Browser instances are now restarted only after a configurable number of consecutive bans or challenge responses, replacing the
  previous fixed-request restart strategy.
* **Static asset blocking (`BROWSER_STATIC_ASSETS_BLOCK`)**
  Optional blocking of images, fonts, stylesheets, and other non-essential assets via Chrome DevTools Protocol, reducing bandwidth
  usage and improving page load performance.
* **`StealthDependencyError`**
  New typed exception for optional dependency loading failures, providing platform-specific guidance for resolving missing native
  libraries and runtime dependencies.

### Fixed

* **Windows browser restart race condition**
  Resolved event-loop teardown and restart timing issues that could produce `InvalidStateError` exceptions during browser restarts.
* **Windows dependency loading failures**
  Improved handling of `wreq` and `curl_cffi` DLL loading errors with actionable error messages instead of opaque import tracebacks.
* **Deferred dependency loading**
  Optional browser-profile dependencies are now loaded lazily, preventing unrelated engines from failing when specific native
  dependencies are unavailable.
* **Browser response rendering**
  Improved response handling to ensure successful pages are fully rendered before being returned to Scrapy.

### Changed

* **Browser restart strategy**
  Replaced the request-count-based restart mechanism with ban-aware restart logic, reducing unnecessary browser restarts during healthy
  crawls.
* **Test suite refactoring**
  Simplified browser-related test cases and reduced mock complexity for improved maintainability.

### Performance

* **Reduced bandwidth consumption**
  Static asset blocking can significantly decrease network usage and page load times when visual assets are not required.
* **Improved browser stability**
  Smarter restart behavior reduces browser churn while maintaining long-running crawl reliability.

## [0.6.8b2] - 2026-06-18

### Added

- **`StealthDependencyError` — typed exception for compiled-dependency failures**
  New exception class in `exceptions.py` that inherits from both `StealthException` and
  `ImportError`, fitting naturally into both the package exception hierarchy and standard
  `except ImportError` handlers.
  Raised whenever a compiled optional dependency (`wreq`, `curl_cffi`) fails to load —
  typically because a required native DLL or shared library could not be found.

  The exception provides a platform-aware, actionable message at raise time:
    - **Windows** — instructs the user to install both x64 and x86 Visual C++ Redistributables
      (2015–2022) with direct download links.
    - **Linux** — suggests the appropriate `apt-get` / `yum` packages for missing system
      libraries (`libssl`, `libcurl`).

  `StealthDependencyError` is exported from the top-level package and added to `__all__`,
  making it catchable in user code alongside the other stealth exceptions.

### Fixed

- **`engines/basic.py` — `ImportError: DLL load failed while importing wreq` on fresh Windows**
  The bare `from wreq.blocking import Client` and `from wreq.proxy import Proxy` module-level
  imports crashed immediately on machines without the Visual C++ Redistributable installed,
  surfacing as an opaque `DLL load failed` traceback deep inside Scrapy's middleware loader.
  Both imports are now wrapped in `try/except ImportError` and delegate to
  `StealthDependencyError.check("wreq", exc)` for a clear, actionable error message.

- **`engines/turbo.py` — same DLL failure for `curl_cffi` on fresh Windows**
  `from curl_cffi import CurlHttpVersion` and `from curl_cffi.requests import Session` suffer
  the same failure path as `wreq` when the VCRT is absent.
  Both imports are now guarded with `StealthDependencyError.check("curl_cffi", exc)`.

- **`utils/profiles.py` — `wreq.emulation` crash at import time propagated silently**
  `from wreq.emulation import Emulation, Profile` was a module-level import, meaning the
  entire `profiles` module — and by extension every engine that imports it — failed to load
  on VCRT-missing machines, producing the same deep `DLL load failed` traceback.
  The import is now guarded with a `_WREQ_AVAILABLE` flag; `Emulation` and `Profile` fall
  back to `None` so the module loads cleanly. The private `_require_wreq()` helper raises
  `StealthDependencyError` at the point of actual use (inside `_resolve_basic`), not at
  import time, keeping the `turbo` and `browser` drivers unaffected on machines where
  `wreq` is broken but `curl_cffi` loads fine.

---

## [0.6.8b1] - 2026-06-16

### Added

- **Intelligent browser restart (`BROWSER_RESTART_AFTER_BANS`)**
  The browser engine now restarts Chrome (fresh fingerprint, cookies, and CDP session) only
  when it actually needs to — after `BROWSER_RESTART_AFTER_BANS` (default `5`) *consecutive*
  responses are classified as banned or challenged by `AntiBotDetector`. A single clean
  response resets the streak to zero, so a browser sailing through cleanly is never restarted,
  no matter how many requests it has served. Replaces the previous fixed-count
  `BROWSER_RESTART_EVERY` restart, which fired blindly every N requests regardless of whether
  anything was actually going wrong.
  Implemented via a small `BanStreakTracker` helper in `utils/browser.py`.

### Fixed

- **Browser engine — restart/teardown race on Windows**
  `_reset_browser()` now waits for the old event loop's thread to fully stop (`_stop_loop()`)
  before starting a new loop and thread. Previously the old `ProactorEventLoop` could keep
  polling its selector after the replacement loop was already running, surfacing as an
  `InvalidStateError` crash or unretrieved `OSError` task exceptions on Windows.

## [0.6.8a1] - 2026-06-12

### Added

- **Intelligent content wait (`_smart_wait`)**
  The browser engine now detects if a page is a JS challenge, CAPTCHA, or script-heavy stub
  (e.g., Cloudflare, DataDome) and automatically waits for the real content to populate.
  It uses a heuristic based on body length and tag structure to decide whether to wait,
  significantly improving success rates on protected sites while maintaining speed on
  normal pages.
- **JS challenge detection (`_JS_IS_CHALLENGE`)**
  A comprehensive JavaScript-based detector that identifies common anti-bot platforms
  (Cloudflare, DataDome, Akamai, Kasada) and challenge states (Ray ID, "Checking your browser")
  by scanning the DOM and window title.
- **Randomized browser fingerprinting**
  Chrome is now launched with randomized `--window-size` and `--lang` arguments selected from
  a curated list of common configurations. This ensures that every browser session (and
  every proxy-rotated request) presents a unique, realistic identity to anti-bot systems.

### Changed

- **Refactored test cases**
  Simplified fetch mocks in tests by removing the unnecessary proxy argument and
  streamlining assertions.

### Fixed

- **Browser engine — improved response handling**
  Integrated `_smart_wait` into the fetch pipeline, ensuring 2xx responses are fully
  rendered before returning.

## [0.6.7] - 2026-06-10

### Changed

- **Browser engine — single persistent browser for both proxy and non-proxy modes**
  Previously, proxy mode spawned a fresh Chrome process for every request and tore it down
  immediately after, making concurrent proxy crawls extremely expensive. The engine now runs
  one persistent browser regardless of whether a proxy is configured.
  A local auth-injecting relay (`_start_proxy_relay`) is started once at browser initialisation
  and the browser is launched with `--proxy-server=http://127.0.0.1:<relay_port>` baked in.
  Each request opens an isolated tab (via `new_tab=True`) and closes it when done — identical
  to non-proxy mode. Proxy credentials are injected at the TCP level by the relay and never
  touch the browser.
  Impact: one Chrome process per spider instead of one per request; dramatically lower memory
  and startup overhead on proxy-enabled crawls.
- **Browser engine — splash screen loaded once at startup, not per request**
  The project logo / `chrome://welcome` splash was previously loaded in every request tab as a
  warm-up step before navigating to the real target. It is now loaded once on `browser.main_tab`
  immediately after the browser starts (`_start()`), warming up the renderer, stealth patches,
  and (when proxied) the relay tunnel — before any spider request arrives. Request tabs navigate
  directly to the target URL with no splash overhead.
- **Browser engine — early return on non-2xx responses**
  `_do_fetch` now reads the HTTP status code before waiting for page content. Responses in the
  2xx range receive the full `_wait_for_content()` + settle delay as before. Non-2xx responses
  (4xx, 5xx) skip the content wait and return immediately with whatever the browser has already
  rendered, avoiding up to 10 seconds of unnecessary polling on error pages.

### Added

- **`_wait_for_status(page, timeout=8.0)` utility**
  The Navigation Timing API (`performance.getEntriesByType('navigation')[0].responseStatus`)
  is written asynchronously by Chrome and can return `0` immediately after `page.wait()`,
  especially through a proxy or after redirects. The new helper polls every 250 ms until a
  non-zero status is available, then returns it. If the entry never populates within 8 seconds
  (rare SPA edge case) it falls back to `200` — the safest assumption when the page loaded but
  left no timing entry. `_JS_STATUS` default changed from `?? 200` to `?? 0` to expose the
  "not ready" state to the poller rather than masking it.

### Fixed

- **Browser engine — `ConnectionResetError` / `BrokenPipeError` log noise on Windows**
  On Windows with Python 3.13+, closing a Chrome tab or stopping the browser triggers
  `_ProactorBasePipeTransport._call_connection_lost()` which raises
  `ConnectionResetError: [WinError 10054] An existing connection was forcibly closed by the
  remote host`. This is harmless — the connection is already gone — but asyncio logged it as
  an unhandled exception on every tab close. The loop exception handler now suppresses
  `ConnectionResetError`, `BrokenPipeError`, and raw `OSError` with `winerror == 10054`
  (the unwrapped variant seen on some Python 3.14 builds).
- **Browser engine — relay and tab-semaphore torn down correctly on browser restart**
  `_reset_browser()` now closes the proxy relay server and clears `_relay_server` /
  `_relay_port` before spinning up a new event loop, so the restarted browser gets a fresh
  relay rather than pointing at a dead port.

## [0.6.6] - 2026-06-08

### Added

- **`BROWSER_EXECUTABLE_PATH` configuration option**
  New setting allows specifying a custom Chrome/Chromium/Brave binary path for the browser engine.
  Set via `config.BROWSER_EXECUTABLE_PATH` or `BROWSER_EXECUTABLE_PATH` in Scrapy settings.
  Useful when Chrome is installed in a non-standard location or when using alternative browsers like Brave.
  Proper error messages guide users to set the config if the binary is not found at the configured path.

- **Unified logger output for browser engine**
  Replaced direct `console` module usage with `logger` throughout the browser engine for consistent,
  structured logging that integrates with Scrapy's logging system. All browser startup messages,
  restarts, and warnings now appear in the standard `[scrapy-stealth]` log format.

### Changed

- **Browser engine — simplified stealth approach for improved detection evasion**
  The `BrowserEngine` has been streamlined to focus on real Chrome behavior without aggressive JavaScript injection.
  Removed the `_STEALTH_JS` injection (which masked CDP fingerprints and spoofed Windows platform attributes)
  because anti-bot systems increasingly detect the injections themselves rather than the CDP presence.

  The engine now:
    - Removes all custom user-agent forcing (uses Chrome's default)
    - Eliminates JavaScript navigator property overrides (`webdriver`, `platform`, `plugins`, `languages`, WebGL, UAv4)
    - Simplifies browser arguments to essential flags only (disables only `AutomationControlled` blink feature)
    - Maintains Xvfb support for non-headless Chrome on Linux without `$DISPLAY`
    - Keeps persistent browser reuse for performance
    - Works identically in headless and non-headless modes

  Result: `headless=False` with real display/Xvfb now evades detection more effectively because
  the browser appears "normal" to anti-bot systems rather than heavily modified.

### Fixed

- **Browser engine — bans when using `headless=False` with injection-based detection**
  Anti-bot systems like Akamai specifically scan for the telltale patterns in commonly-used CDP stealth scripts.
  Removing the injection eliminates a major detection surface while maintaining the evasion benefits of running
  a real browser process.

### Optimized

- **Browser engine — code duplication eliminated**
  Extracted `_start_browser()` helper method that centralizes browser startup and `BROWSER_EXECUTABLE_PATH`
  error handling. `_start()` (persistent browser) and `_do_fetch()` (per-proxy browser) now call the same
  code path, reducing maintenance burden and ensuring consistent behavior across non-proxy and proxy modes.

---

## [0.6.6a2] - 2026-06-04

### Added

- **Xvfb virtual display support for Docker / Zyte**
  On Linux without a `$DISPLAY`, the browser engine now automatically starts
  `Xvfb :99` before launching Chrome. This lets Chrome run in non-headless mode
  against a virtual framebuffer — identical to a real desktop session — which is
  significantly harder for anti-bot systems to detect than `--headless=new`.
  Falls back to headless silently if Xvfb is not installed.
  Requires `apt-get install -y xvfb` in your Docker image.

---

## [0.6.6a1] - 2026-06-04

### Added

- **`BROWSER_NO_SANDBOX` config option**
  New `BROWSER_NO_SANDBOX: bool | None` setting controls Chrome's sandbox mode.
  Defaults to `None` (auto-detect): sandbox is disabled automatically when the process runs
  as root on Linux (e.g. Zyte, Docker). Set `True` to force no-sandbox, `False` to keep
  sandbox even as root. Configurable via `settings.py` (`BROWSER_NO_SANDBOX = True`) or
  the `config` object.

### Fixed

- **Browser engine fails on Zyte / Docker (running as root)**
  Chrome refuses to start without `--no-sandbox` when the process is root. The engine now
  auto-detects root and adds both `--no-sandbox` and `--disable-dev-shm-usage` (required
  in containers with limited `/dev/shm`).

- **`headless=False` crashes in display-less environments**
  When no `$DISPLAY` is set on Linux (Docker, Zyte, CI), the engine now silently overrides
  `headless=False` to `headless=True`, preventing Chrome from crashing on startup.

---

## [0.6.5] - 2026-06-01

### Fixed

- **`patch_nodriver()` now safe to run multiple times**
  The previous implementation used `importlib.util.find_spec("nodriver.cdp.network")` which
  itself triggered the `SyntaxError` it was trying to fix (importing the submodule requires
  importing the parent, which fails). Switched to `find_spec("nodriver")` (top-level only)
  and constructing the path to `cdp/network.py` via `pathlib`. Additionally, the replacement
  now uses a regex negative lookbehind `(?<!\xc2)\xb1` to prevent double-encoding on
  subsequent runs.

- **Browser engine: handle tab/browser closed mid-request**
  Two new exception types are now caught and raised as `StealthConnectionError` instead of
  logging as unhandled errors:
    - `ConnectionClosedError` — WebSocket dropped (tab closed while loading)
    - `ProtocolException` — CDP target no longer found (tab/context destroyed)

---

## [0.6.4] - 2026-05-21

### Added

- **Auto-patch for `nodriver` encoding bug**
  `scrapy_stealth.utils.patch.patch_nodriver()` is now called automatically when the browser
  engine is first imported. It detects and fixes the Latin-1 byte (`\xb1`) in
  `nodriver/cdp/network.py` that causes a `SyntaxError` on Python 3 without an encoding
  declaration. The patch is re-applied after every `pip install --upgrade nodriver` without
  any manual intervention required.

### Fixed

- **`StealthTimeoutError` compatibility with Scrapy < 2.15**
  `scrapy.exceptions.DownloadTimeoutError` was added in Scrapy 2.15. Importing it directly
  caused an `ImportError` on older Scrapy versions (e.g. 2.12–2.14). `StealthTimeoutError`
  now falls back to `TimeoutError` as its base class when `DownloadTimeoutError` is not
  available, keeping full compatibility across all supported Scrapy versions.

### Changed

- **Shorter middleware import path**
  `StealthDownloaderMiddleware` is now importable directly from the top-level package:

  ```python
  DOWNLOADER_MIDDLEWARES = {
      "scrapy_stealth.StealthDownloaderMiddleware": 950,
  }
  ```

  The full path `scrapy_stealth.middlewares.stealth.StealthDownloaderMiddleware` still works
  for backwards compatibility.

---

## [0.6.3] - 2026-05-20

### Added

- **`STEALTH_ENABLED` — global stealth mode**
  New Scrapy setting that routes all requests through the stealth engine automatically — no need
  to add `meta={"stealth": {...}}` on every request. Set once in `settings.py` or `custom_settings`:

  ```python
  STEALTH_ENABLED = True
  ```

  Per-request opt-out is still supported via `meta={"stealth": False}`.
  `STEALTH_ENABLED` is also read from `spider_opened` so `custom_settings` on the spider class
  takes effect without restarting the crawler process.

- **`STEALTH_DRIVER` — engine driver configurable from Scrapy settings**
  The default stealth driver (`"basic"`, `"turbo"`, or `"browser"`) can now be set globally in
  `settings.py` or `custom_settings` instead of per-request:

  ```python
  STEALTH_DRIVER = "turbo"
  ```

  `spider_opened` reads this setting and applies it to `config.STEALTH_DRIVER` at spider start.

- **`StealthResponse` — engine name in response flags**
  Every `StealthResponse` now includes the engine driver name in its Scrapy `flags` list alongside
  the package logger name (e.g. `["scrapy-stealth", "turbo"]`). The flag appears in Scrapy's
  crawl log next to each response line, making it easy to see which engine handled each request.

### Fixed

- **`EngineManager.get()` — `KeyError` crash on invalid driver**
  When `STEALTH_DRIVER` was set to a typo (e.g. `"browsesr"`) the fallback path also read
  `config.get("STEALTH_DRIVER")`, which returned the same invalid value, causing a `KeyError`.
  The fallback now uses `_DEFAULT_DRIVER` from `constants` (the package-level safe default),
  with `config.STEALTH_DRIVER` preferred when it is itself valid.

---

## [0.6.2] - 2026-05-20

### Added

- **Custom engine exceptions — `StealthTimeoutError`, `StealthConnectionError`, `StealthBrowserNotFoundError`**
  All three engines previously swallowed non-standard library exceptions and returned `None`, silently
  bypassing Scrapy's retry middleware. Three typed exceptions now replace raw library errors:

  | Exception                     | Inherits from                 | Retried by Scrapy                           | Raised by                                                                             |
                        |-------------------------------|-------------------------------|---------------------------------------------|---------------------------------------------------------------------------------------|
  | `StealthTimeoutError`         | `DownloadTimeoutError`        | ✅ (in default `RETRY_EXCEPTIONS`)           | All engines on request timeout                                                        |
  | `StealthConnectionError`      | `ConnectionError` → `OSError` | ✅ (`OSError` in default `RETRY_EXCEPTIONS`) | `BasicEngine` / `TurboEngine` on DNS or network failure; `BrowserEngine` on `OSError` |
  | `StealthBrowserNotFoundError` | `StealthException` only       | ❌ (config error, retrying is pointless)     | `BrowserEngine` when Chrome/Chromium binary is missing                                |

  Library-specific exceptions (`curl_cffi.Timeout`, `wreq.TimeoutError`, `wreq.ConnectionError`,
  `curl_cffi.ConnectionError`, `curl_cffi.DNSError`, `curl_cffi.ProxyError`, `wreq.ProxyConnectionError`)
  are caught and re-raised as the appropriate stealth exception, preserving the original as `__cause__`.
  All three are exported from `scrapy_stealth` and can be caught in spider `errback` handlers.

- **`BrowserEngine` — Chrome error page detection**
  When a target URL is unreachable (DNS failure, network down), Chrome silently navigates to
  `chrome-error://chromewebdata/` instead of raising a Python exception. The engine now evaluates
  `window.location.href.startsWith('chrome-error://')` immediately after navigation; if true,
  `StealthConnectionError` is raised so Scrapy's retry middleware handles it correctly.

### Fixed

- **Zyte (ScrapyCloud) — `FileException: download-error` on `scrapy:2.15` stack**
  `BaseEngine.fetch()` used Twisted's `deferToThread` to run blocking HTTP calls in a thread pool.
  On Scrapy 2.15 / Python 3.14, the media pipeline's fully-async architecture relies on native
  asyncio awaiting; the Twisted→asyncio bridge no longer reliably resolved these Deferreds, causing
  file/image downloads to fail with `FileException("download-error")`.
  `BaseEngine.fetch()` is now `async def` and uses `asyncio.get_running_loop().run_in_executor()`.
  `ScrapyEngine.fetch()` and `StealthDownloaderMiddleware.process_request()` are also made `async`.

- **Zyte (ScrapyCloud) — `ImportError: cannot import name 'request_fingerprint'` on `scrapy:2.11` stack**
  The previous `scrapy>=2.15.2` constraint forced pip to upgrade Scrapy on Zyte's `scrapy:2.11`
  stack, which broke Zyte's bundled `sh_scrapy` extension that still imports `request_fingerprint`
  (removed in Scrapy 2.15). The constraint is now `scrapy>=2.12.0,<3.0`.

- **All Scrapy versions — unified async dispatch in `BaseEngine.fetch`**
  Scrapy routes async downloader middlewares through different runners depending on version:
  `ensure_awaitable` (newer Scrapy / local) runs coroutines as asyncio Tasks and requires an
  asyncio Future; `deferred_from_coro` (Zyte `scrapy:2.11–2.12`) drives them via Twisted
  `_inlineCallbacks` and requires a Twisted Deferred. `BaseEngine.fetch` now detects the active
  runner via `asyncio.get_running_loop()` and dispatches to `run_in_executor` or `deferToThread`
  accordingly, making stealth requests work correctly on all supported Scrapy versions.

- **`TurboEngine` / `BasicEngine` — timeout exceptions silently swallowed**
  `curl_cffi.requests.exceptions.Timeout` and `wreq.exceptions.TimeoutError` are not subclasses
  of Python's built-in `TimeoutError`, so the `except TimeoutError: raise` guard did not catch
  them. Both were swallowed by the broad `except Exception` handler and discarded as `None`,
  preventing Scrapy's retry middleware from ever seeing a timeout. Both engines now raise
  `StealthTimeoutError` for their respective library timeout types.

- **`RequestContext` (`ctx`) moved before `try` block in all engines**
  `ctx = self._ctx(request)` was inside the `try` block, causing IDE warnings about possible
  reference before assignment when `ctx` was used in `except` handler messages.

---

## [0.6.1] - 2026-05-18

### Fixed

- **Zyte (ScrapyCloud) — `ValueError: invalid literal for int()` on `download_latency`**
  `BaseEngine._execute_timed` stored download latency as a formatted string (`"0.18s"`) instead of a numeric value. Zyte's `sh_scrapy`
  pipe writer calls `int(duration)` and expects a plain number; the string caused a `ValueError` at response write time, and the string
  was repeated across concurrent/retried requests making it unreadable.
  `download_latency` is now stored as a plain `float` (e.g. `0.18`), consistent with Scrapy's own HTTP downloader.

### Added

- **`utils/meta_info.py` — `PackageMetadata` utility**
  Frozen dataclass that reads `name`, `version`, `author`, `email`, `license`, `summary`, and `homepage` from the installed
  distribution metadata via `importlib.metadata`.
  Parses `"Name <email>"` author strings with a regex, picks the first available URL field, and falls back to compile-time defaults
  when the package is not installed (e.g. running from source without `pip install -e .`).
  A module-level singleton `_pkg_meta` is resolved once at import time; `__init__.py` now derives `__version__`, `__author__`, and
  `__license__` from it. `PackageMetadata` is exported in `__all__`.

---

## [0.6.0] - 2026-05-12

### Fixed

- **Browser engine — `StopIteration` / `RuntimeError` crash under concurrent load**
  `browser.get(url)` without `new_tab=True` reused the persistent main tab; after `page.close()` the main tab was destroyed, so the
  next call to `browser.get()` found no `"page"` targets and raised `StopIteration` inside a coroutine (→
  `RuntimeError: coroutine raised StopIteration`).
  All fetches now use `browser.get(url, new_tab=True)` — each request gets its own isolated tab, the main tab stays alive permanently,
  and `StopIteration` can never occur.

- **Browser engine — noisy `[asyncio] ERROR: Task exception was never retrieved` spam**
  nodriver fires background `update_targets()` tasks on a timer; when Chrome restarts these tasks raise `ConnectionRefusedError` which
  asyncio logs as unhandled task exceptions.
  A custom loop exception handler now suppresses `ConnectionRefusedError` from the browser event loop, eliminating the log noise.

- **Browser engine — automatic crash recovery**
  On `ConnectionRefusedError` (Chrome process died) the engine now restarts the browser and retries the current request once before
  giving up.
  A dead-browser guard (`dead_browser` parameter on `_reset_browser`) prevents multiple concurrent threads from each triggering a
  redundant restart.

### Added

- **`BROWSER_MAX_TABS`** (default `10`) — caps the number of Chrome tabs open simultaneously via an asyncio `Semaphore`, preventing
  Chrome from being overwhelmed when Scrapy fires many concurrent requests.
  Configurable via `config.BROWSER_MAX_TABS` or `constants.BROWSER_MAX_TABS`.

- **`BROWSER_RESTART_EVERY`** (default `200`) — proactively restarts Chrome every N requests to prevent memory bloat on long
  high-volume runs.
  Configurable via `config.BROWSER_RESTART_EVERY` or `constants.BROWSER_RESTART_EVERY`.

- **`utils/session.py` — `SessionCache[K, V]`** — generic lazy per-thread cache backed by a factory callable.
  Each Twisted thread pool thread maintains its own isolated dict; the factory is called once per key per thread and the result is
  reused on every subsequent call from that thread.
  Eliminates the boilerplate `threading.local()` + `hasattr` + dict pattern that both `BasicEngine` and `TurboEngine` previously
  duplicated.

### Changed

- **`TurboEngine` — persistent thread-local sessions** (performance)
  Previously a fresh `Session` was created and destroyed for every request, incurring a full TLS handshake cost each time.
  Sessions are now cached per `(thread, impersonation-profile)` via `SessionCache`, enabling TCP connection reuse and TLS session
  resumption within each Twisted thread pool thread.

- **`BasicEngine` — thread-local clients** (correctness + performance)
  The previous `self._clients: dict[bool, Client]` was shared across all Scrapy threads, creating a potential concurrent-write race on
  first use and preventing per-thread connection pooling.
  Replaced with `SessionCache` — each thread gets its own `wreq.Client` per http2 setting.

- **`BROWSER_MAX_TABS` and `BROWSER_RESTART_EVERY`** added to `constants.py` and registered as `StealthConfig` attributes so they are
  accessible via `config.get()` like all other browser settings.

---

## [0.5.0] - 2026-05-11

### Added

#### Real Browser Engine (`driver="browser"`)

A third stealth driver powered by a real Chrome instance via the Chrome DevTools Protocol (no WebDriver).
Designed for Cloudflare-protected pages, heavy JavaScript SPAs, and any site that defeats HTTP-level impersonation.

Key characteristics:

- **No WebDriver** — communicates over CDP directly; `navigator.webdriver` is never set
- **Persistent browser, tab-per-request** — one Chrome process is reused across requests; each request opens a new tab and closes it
  when done, keeping memory overhead low
- **Proxy isolation** — when a proxy is set, a fresh browser is started per request so every request exits from a different IP with no
  shared state
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
- `TurboEngine` — new stealth engine driver using new techs for impersonation; strips Scrapy fingerprint headers before passing to the
  driver so its own TLS profile is not overridden
- `config.STEALTH_DRIVER` — global default driver (`"basic"` or `"turbo"`); overridable per-request via `request.meta["driver"]`
- `request.meta["driver"]` — per-request driver override (`"basic"` or `"turbo"`)
- Generic profile resolver in `utils/profiles.py` — `resolve_browser(profile, backend)` returns a basic `Profile` for `"basic"` or a
  turbo impersonation string for `"turbo"`;
- `response.meta["download_latency"]` — stealth engines automatically inject download latency (formatted as `"1.02s"`) into the
  response meta,
- `BaseEngine._execute_timed` — internal wrapper that times every `_execute` call and writes `download_latency` into the response meta;
  all current and future engines inherit this for free
- `StealthResponse._meta` parameter — accepts an optional dict merged into a copy of `request.meta` before building the response,
  allowing engines to inject stealth-specific keys without mutating the original request
- Python 3.14 support — added `Programming Language :: Python :: 3.14` classifier to `pyproject.toml`
- CI matrix extended with Python 3.14 and OS compatibility jobs for Windows and macOS (Python 3.14 only); all Python versions continue
  to run on Ubuntu

### Changed

- `engines/basic.py` (renamed from `engines/browser.py`) — `BasicEngine` replaces `BrowserEngine`; imports updated to
  `utils/profiles.py`
- `utils/profiles.py` (renamed from `utils/browsers.py`) — profile resolution is now backend-aware; both drivers share the same profile
  name space
- `EngineManager` — updated to instantiate and cache both `BasicEngine` and `TurboEngine`; unknown driver falls back to `BasicEngine`
- `StealthDownloaderMiddleware` — reads `meta["driver"]` and passes it to `EngineManager.get(engine_name, driver)`
- `utils/meta.py` — `"driver"` added to `_STEALTH_ONLY_KEYS` so misuse warnings are emitted when it is set without `engine="stealth"`
- `StealthResponse.encoding` is now dynamic — `TurboEngine` passes `resp.encoding` from response; `BasicEngine` passes `None` so Scrapy
  auto-detects from headers and body; hardcoded `"utf-8"` fallback removed
- `BaseEngine.fetch` — now delegates to `_execute_timed` instead of `_execute` directly so latency tracking is transparent to all
  subclasses
- Downloads badge in README switched from `shields.io` to `pepy.tech` to avoid upstream rate-limit errors
- Dependencies: `NL` added to `pyproject.toml`

### Fixed

- `ScrapyEngine` — implemented the `_execute` abstract method (was raising
  `TypeError: Can't instantiate abstract class ScrapyEngine without an implementation for abstract method '_execute'` at spider
  startup)

### Tests

- Added 13-test suite for `TurboEngine` covering: response type, HTTP/1.1 and HTTP/2 version selection, fingerprint header stripping,
  proxy passthrough, body passthrough on POST, turbo profile resolution, exception handling, `TimeoutError` re-raise, and
  `content-encoding` header removal

---

## [0.2.2] - 2026-04-28

### Added

- HTTP/2 support for the stealth engine — enabled by default (`HTTP2 = True` in `StealthConfig`); disable globally via
  `config.HTTP2 = False` or per-request via `request.meta["http2"] = False`
- `BasicEngine._get_client` — lazy per-protocol client cache; separate `Client` instances are created for HTTP/1.1 and HTTP/2 on first
  use

### Changed

- `BasicEngine` — improved stealth client creation log from generic bracket notation to structured `key=value` format:
  `"Initializing stealth HTTP client (protocol=%s)"`
- `StealthConfig.LOGGER_NAME` — annotated as `Final[str]` to signal immutability; type checkers will flag any attempt to reassign it

---

## [0.2.1] - 2026-04-27

### Fixed

- `BasicEngine.__init__` — `profile` and `timeout` parameters now default to `None` (sentinel) and resolve from `config` at call time,
  fixing the Python mutable-default anti-pattern that caused runtime `config` changes to be ignored
- `BasicEngine._execute` — removed duplicate `config.get("DEFAULT_PROFILE")` lookup; now uses `self._default_profile` as the single
  source of truth; `resolve_browser` is skipped when the per-request profile matches the engine default
- `resolve_browser` — removed `None` handling from the function signature (`str | Profile | None` → `str | Profile`); callers are now
  responsible for resolving defaults before calling, eliminating an implicit config dependency inside the utility

### Changed

- `StealthConfig` test coverage extended to include `BLOCK_CODES`, `BLOCK_KEYWORDS`, `LOGGER_NAME`, `get()` method, and the `config`
  singleton
- All config-driven values in tests (`DEFAULT_ENGINE`, `DEFAULT_PROFILE`, block codes, etc.) now reference `config.get()` instead of
  hardcoded strings, so tests stay correct if defaults change
- README: added **Global Configuration** section documenting the `config` singleton, all `StealthConfig` attributes with types and
  defaults, and `config.get()` usage

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

[0.6.13]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.13

[0.6.12]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.12

[0.6.11]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.11

[0.6.11a1]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.11a1

[0.6.10]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.10

[0.6.10a2]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.10a2

[0.6.10a1]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.10a1

[0.6.8b2]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.8b2

[0.6.8b1]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.8b1

[0.6.8]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.8

[0.6.7]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.7

[0.6.1]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.1

[0.6.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.6.0

[0.5.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.5.0

[0.4.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.4.0

[0.3.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.3.0

[0.2.2]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.2

[0.2.1]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.1

[0.2.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.2.0

[0.1.0]: https://github.com/fawadss1/scrapy-stealth/releases/tag/v0.1.0
