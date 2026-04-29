"""
scrapy-stealth: A pluggable anti-bot and stealth framework for Scrapy.

Quick start
-----------
Add the middleware to your settings.py or spider custom_settings::

    DOWNLOADER_MIDDLEWARES = {
        "scrapy_stealth.middlewares.stealth.StealthDownloaderMiddleware": 950,
    }

    # Optional: proxy list for automatic rotation
    STEALTH_PROXIES = [
        "http://proxy1:8080",
        "socks5://proxy2:1080",
    ]

Per-request usage via ``request.meta``::

    yield scrapy.Request(
        url,
        meta={
            "engine": "stealth",
            "rotate_profile": True,   # auto-select a browser fingerprint
            "rotate_proxy": True,     # auto-select a proxy from STEALTH_PROXIES
        },
    )

Note: ``rotate_profile``, ``rotate_proxy``, and ``profile`` have no effect
unless ``engine`` is set to ``"stealth"``. A warning is logged if they are used
with the default scrapy engine.
"""

from .config import StealthConfig, config
from .constants import (
    BLOCK_CODES,
    BLOCK_KEYWORDS,
    DEFAULT_ENGINE,
    DEFAULT_PROFILE,
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

__version__ = "0.2.0"
__author__ = "Fawad Ali"
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
    "DEFAULT_PROFILE",
    "DEFAULT_TIMEOUT",
    # Exceptions
    "StealthException",
    "EngineNotFound",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
