from __future__ import annotations

from ..config import config

# Signatures that identify JS-only challenge pages (Akamai, Cloudflare, DataDome, etc.)
_JS_CHALLENGE_SIGS: tuple[str, ...] = (
    "sec-if-cpt-container",   # Akamai
    "behavioral-content",     # Akamai
    "cf-browser-verification",  # Cloudflare
    "just a moment",          # Cloudflare
    "__cf_chl",               # Cloudflare
    "datadome",               # DataDome
    "px-captcha",             # PerimeterX
    "location.reload(true)",  # generic JS reload challenge
)


def is_blocked(response) -> bool:
    if response.status in config.get("BLOCK_CODES"):
        return True
    body = response.text.lower()
    return any(kw in body for kw in config.get("BLOCK_KEYWORDS"))


def is_js_challenge(body: str) -> bool:
    """Return True if the response body is a JavaScript-only anti-bot challenge page."""
    body_lower = body.lower()
    return any(sig in body_lower for sig in _JS_CHALLENGE_SIGS)
