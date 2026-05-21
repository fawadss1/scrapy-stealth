try:
    from scrapy.exceptions import DownloadTimeoutError as _DownloadTimeoutError
except ImportError:
    _DownloadTimeoutError = TimeoutError


class StealthException(Exception):
    """Base exception for scrapy-stealth."""


class EngineNotFound(StealthException):
    """Raised when engine is not registered."""


class StealthTimeoutError(StealthException, _DownloadTimeoutError):
    """Raised when a stealth engine request times out."""


class StealthConnectionError(StealthException, ConnectionError):
    """Raised when a stealth engine fails to connect (DNS, network, proxy)."""


class StealthBrowserNotFoundError(StealthException):
    """Raised when the browser binary is not found on the system."""
