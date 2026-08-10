from __future__ import annotations

from ...config import config

# Signatures that identify JS-only challenge pages (Akamai, Cloudflare, DataDome, etc.)
_JS_CHALLENGE_SIGS: tuple[str, ...] = (
    "sec-if-cpt-container",  # Akamai
    "behavioral-content",  # Akamai
    "cf-browser-verification",  # Cloudflare
    "just a moment",  # Cloudflare
    "__cf_chl",  # Cloudflare
    "datadome",  # DataDome
    "px-captcha",  # PerimeterX
    "location.reload(true)",  # generic JS reload challenge
)

# Matches _CONTENT_SHORT_THRESHOLD in utils/browser/_core.py — pages shorter than this
# with anti-bot markers are treated as challenge stubs, not real content.
_BROWSER_SHORT_BODY = 2500


def is_blocked(response) -> bool:
    if response.status in config.get("BLOCK_CODES"):
        return True
    body = response.text.lower()
    return any(kw in body for kw in config.get("BLOCK_KEYWORDS"))


def is_js_challenge(body: str) -> bool:
    """Return True if the response body is a JavaScript-only anti-bot challenge page."""
    body_lower = body.lower()
    return any(sig in body_lower for sig in _JS_CHALLENGE_SIGS)


def is_browser_session_ban(response) -> bool:
    """
    True when a browser response means the Chrome session should be recycled.

    HTTP block codes always count. Keyword and JS-challenge heuristics apply
    only to short pages — large HTTP 200 documents may embed anti-bot scripts
    (e.g. DataDome) while still being valid product pages.
    """
    if response.status in config.get("BLOCK_CODES"):
        return True
    if len(response.body) >= _BROWSER_SHORT_BODY:
        return False
    if response.status >= 400:
        return is_blocked(response)
    body = response.text
    return is_js_challenge(body) or any(
        kw in body.lower() for kw in config.get("BLOCK_KEYWORDS")
    )
