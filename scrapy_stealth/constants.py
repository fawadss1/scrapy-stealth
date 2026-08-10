from __future__ import annotations

from .utils.meta_info import _pkg_meta

# HTTP status codes that indicate an anti-bot block or rate-limit.
# Used by both the retry logic and the anti-bot detector.
BLOCK_CODES: frozenset[int] = frozenset({403, 429, 503})

# Body text patterns that signal an anti-bot challenge page.
BLOCK_KEYWORDS: list[str] = [
    "captcha",
    "access denied",
    "verify you are human",
    "robot check",
    "are you a human",
    "security check",
    "ddos protection",
    "please verify",
    "unusual traffic",
]

# Default browser profile used when no profile is specified.
DEFAULT_PROFILE: str = "chrome_147"

# Default engine used when no engine is specified in request meta.
DEFAULT_ENGINE: str = "scrapy"

# Default request timeout in seconds.
DEFAULT_TIMEOUT: int = 30

# Logger name used across the entire package — derived from the package name.
LOGGER_NAME = _pkg_meta.name

# Whether the stealth engine uses HTTP/2.
# Disable if targeting servers that only support HTTP/1.1.
HTTP2: bool = True

# Default stealth driver. Options: "basic", "turbo", "browser", or "auto".
# "auto" starts with basic/turbo (see STEALTH_DRIVER when not "auto", else "basic")
# and retries once with the browser driver on JS challenge / session ban.
STEALTH_DRIVER: str = "basic"

# When True, all requests are routed through the stealth engine automatically —
# no need to set meta={"stealth": {...}} on each request.
# Set to True in settings.py or spider custom_settings to enable globally.
# Per-request opt-out: meta={"stealth": False}
STEALTH_ENABLED: bool = False

# When True, basic/turbo responses that look like a JS challenge or session ban
# are retried once with the browser driver (headless=False). Off by default —
# enable globally or per-request with meta["stealth"]["driver"] = "auto".
# Opt out per-request with meta["stealth"]["fallback"] = False.
STEALTH_AUTO_FALLBACK: bool = False

# Proxy pool (also loaded from Scrapy settings ``STEALTH_PROXIES``). Used as the
# engine default proxy and rotated automatically on ban-streak session recycle.
# Explicit meta["stealth"]["proxy"] always wins. Empty = no proxy.
STEALTH_PROXIES: list[str] = []

# Pin destination hosts to fixed IPs (bypass local/public DNS). Connects to the
# given IP while keeping the original hostname for TLS SNI, Host header, and
# certificate verification — useful when public DNS is poisoned, geo-shifted,
# or when you want a stable origin edge. Also readable from Scrapy settings as
# STEALTH_DNS_OVERRIDES. Per-request override via meta["stealth"]["dns"]
# (bare IP for the request host, or a {host: ip} mapping).
# Example: {"example.com": "203.0.113.10", "www.example.com": "203.0.113.10"}
STEALTH_DNS_OVERRIDES: dict[str, str] = {}

# Browser engine: run Chrome headless by default.
BROWSER_HEADLESS: bool = True

# Browser engine: seconds to wait after navigation for JS to finish rendering.
BROWSER_SETTLE_S: float = 4.0

# Browser engine: max Chrome tabs open simultaneously across concurrent requests.
BROWSER_MAX_TABS: int = 10

# After this many *consecutive* banned/challenged responses:
# - browser: restart Chrome (fresh fingerprint, cookies, CDP session)
# - basic / turbo: clear cached HTTP clients/sessions (fresh TLS/cookies)
STEALTH_RECYCLE_AFTER_BANS: int = 5

# Minimum seconds between ban-triggered restarts / session recycles. Stops restart
# loops when every concurrent request keeps returning 403; does not block the
STEALTH_RECYCLE_COOLDOWN_S: float = 15.0

# Browser engine: block static assets (images, fonts, CSS, media) to speed up
# page loads and cut bandwidth. Off by default since some anti-bot checks and
# visual snapshots need them; overridable per-request via
# meta["stealth"]["static_assets_block"]. Always left unblocked when
# meta["stealth"]["snapshot"] is True, regardless of this setting.
BROWSER_STATIC_ASSETS_BLOCK: bool = False

# Browser engine: domains/patterns that must bypass the proxy and connect to the
# origin directly. Passed straight to Chrome's --proxy-bypass-list launch flag
# (entries joined with ';'), so the full Chrome syntax is supported: bare
# hostnames, wildcards ("*.example.com"), IP/CIDR ranges, ports, and the special
# "<local>" token. Only takes effect when a proxy is in use. Set at browser
# launch, so it is read from config / settings (not per-request meta).
BROWSER_PROXY_BYPASS_LIST: list[str] = []

# Browser engine: disable Chrome sandbox (required when running as root, e.g. Docker).
# None = auto-detect: sandbox is disabled automatically when the process runs as root on Linux.
# Set True to force no-sandbox mode; False to keep sandbox even when running as root.
BROWSER_NO_SANDBOX: bool | None = None

# Browser engine: path to the browser executable.
# None = auto-detect: nodriver will locate Google Chrome / Chromium automatically.
# Set to an explicit path to use a different browser binary (e.g. Brave, Chromium, or a
# custom Chrome installation):
#   config.BROWSER_EXECUTABLE_PATH = "/usr/bin/brave-browser"
#   config.BROWSER_EXECUTABLE_PATH = "/opt/chrome/chrome"
BROWSER_EXECUTABLE_PATH: str | None = None
