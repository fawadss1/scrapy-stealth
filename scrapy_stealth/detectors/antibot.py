from __future__ import annotations

from ..utils.antibot import (
    _JS_CHALLENGE_SIGS,
    is_blocked,
    is_browser_session_ban,
    is_js_challenge,
)


class AntiBotDetector:
    """Classifies Scrapy responses as blocked, challenged, or clear."""

    @staticmethod
    def is_blocked(response) -> bool:
        """True if the response is blocked by status code or anti-bot keyword."""
        return is_blocked(response)

    @staticmethod
    def is_js_challenge(response) -> bool:
        """True if the response is a JS-only challenge page that requires a real browser."""
        return is_js_challenge(response.text)

    @staticmethod
    def is_js_challenge_body(body: str) -> bool:
        """Same as is_js_challenge but accepts a raw HTML string instead of a response."""
        return is_js_challenge(body)

    @staticmethod
    def is_browser_session_ban(response) -> bool:
        """True when the browser engine should recycle the Chrome session."""
        return is_browser_session_ban(response)

    @staticmethod
    def reason(response) -> str | None:
        """
        Human-readable reason why this response is blocked or challenged.
        Returns None if the response looks clean.
        """
        from ..config import config

        if response.status in config.get("BLOCK_CODES"):
            return f"HTTP {response.status}"

        body_lower = response.text.lower()

        for kw in config.get("BLOCK_KEYWORDS"):
            if kw in body_lower:
                return f"keyword match: {kw!r}"

        for sig in _JS_CHALLENGE_SIGS:
            if sig in body_lower:
                return f"JS challenge: {sig!r}"

        return None

    def detect(self, response) -> dict:
        """
        Return a full detection summary for the response.

        Returns a dict with keys:
          - ``blocked``      (bool) — status code or keyword block
          - ``js_challenge`` (bool) — JS-only challenge page
          - ``reason``       (str | None) — first matching reason
        """
        return {
            "blocked": self.is_blocked(response),
            "js_challenge": self.is_js_challenge(response),
            "reason": self.reason(response),
        }
