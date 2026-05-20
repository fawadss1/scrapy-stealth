from scrapy.exceptions import DownloadTimeoutError


class StealthException(Exception):
    """Base exception for scrapy-stealth."""


class EngineNotFound(StealthException):
    """Raised when engine is not registered."""


class StealthTimeoutError(StealthException, DownloadTimeoutError):
    """Raised when a stealth engine request times out."""
