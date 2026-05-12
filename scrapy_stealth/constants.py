from __future__ import annotations

from importlib.metadata import PackageNotFoundError, metadata

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
try:
    LOGGER_NAME: str = metadata("scrapy-stealth")["Name"]
except PackageNotFoundError:
    LOGGER_NAME = "scrapy-stealth"

# Whether the stealth engine uses HTTP/2.
# Disable if targeting servers that only support HTTP/1.1.
HTTP2: bool = True

# Default stealth driver. Options: "basic", "turbo", "browser".
STEALTH_DRIVER: str = "basic"

# Browser engine: run Chrome headless by default.
BROWSER_HEADLESS: bool = True

# Browser engine: seconds to wait after navigation for JS to finish rendering.
BROWSER_SETTLE_S: float = 4.0

# Browser engine: max Chrome tabs open simultaneously across concurrent requests.
BROWSER_MAX_TABS: int = 10

# Browser engine: restart Chrome after this many requests to prevent memory bloat.
BROWSER_RESTART_EVERY: int = 200
