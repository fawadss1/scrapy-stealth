class StealthException(Exception):
    """Base exception for scrapy-stealth."""


class EngineNotFound(StealthException):
    """Raised when engine is not registered."""
