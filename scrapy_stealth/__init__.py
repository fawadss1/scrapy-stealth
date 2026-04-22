"""
scrapy-stealth: A pluggable anti-bot and stealth framework for Scrapy.

Quick start
-----------
Add the middleware to your Scrapy settings::

    DOWNLOADER_MIDDLEWARES = {
        "scrapy_stealth.middlewares.stealth.StealthDownloaderMiddleware": 950,
    }

Then enable stealth per-request via ``request.meta``::

    yield scrapy.Request(url, meta={"engine": "stealth", "impersonate": "chrome_137"})
"""

from .config import StealthConfig
from .constants import (
    BLOCK_CODES,
    BLOCK_KEYWORDS,
    DEFAULT_ENGINE,
    DEFAULT_IMPERSONATE,
    DEFAULT_TIMEOUT
)
from .detectors.antibot import AntiBotDetector
from .engines.base import BaseEngine
from .engines.browser import BrowserEngine
from .engines.scrapy import ScrapyEngine
from .exceptions import EngineNotFound, StealthException
from .manager import EngineManager
from .middlewares.stealth import StealthDownloaderMiddleware
from .strategies.fingerprint import ProfileRotator
from .strategies.proxy import ProxyRotator
from .strategies.retry import RetryHandler

__version__ = "0.1.0"
__author__ = "Fawad"
__license__ = "MIT"

__all__ = [
    # Middleware
    "StealthDownloaderMiddleware",
    # Engines
    "BaseEngine",
    "ScrapyEngine",
    "BrowserEngine",
    # Manager
    "EngineManager",
    # Strategies
    "ProxyRotator",
    "ProfileRotator",
    "RetryHandler",
    # Detectors
    "AntiBotDetector",
    # Config
    "StealthConfig",
    # Constants
    "BLOCK_CODES",
    "BLOCK_KEYWORDS",
    "DEFAULT_ENGINE",
    "DEFAULT_IMPERSONATE",
    "DEFAULT_TIMEOUT",
    # Exceptions
    "StealthException",
    "EngineNotFound",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
