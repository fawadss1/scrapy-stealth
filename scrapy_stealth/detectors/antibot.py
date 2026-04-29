from __future__ import annotations

from ..utils.antibot import is_blocked


class AntiBotDetector:
    """Classifies responses as blocked by anti-bot systems."""

    @staticmethod
    def is_blocked(response) -> bool:
        return is_blocked(response)
