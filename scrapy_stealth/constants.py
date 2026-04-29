from __future__ import annotations

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

# Default browser profile used when no impersonation is specified.
DEFAULT_IMPERSONATE: str = "chrome_137"

# Default engine used when no engine is specified in request meta.
DEFAULT_ENGINE: str = "scrapy"

# Default request timeout in seconds.
DEFAULT_TIMEOUT: int = 30
