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

from importlib.metadata import PackageNotFoundError, metadata

from .config import StealthConfig, config
from .detectors.antibot import AntiBotDetector
from .engines.base import BaseEngine
from .exceptions import EngineNotFound, StealthException
from .middlewares.stealth import StealthDownloaderMiddleware
from .strategies.fingerprint import ProfileRotator
from .strategies.proxy import ProxyRotator
from .strategies.retry import RetryHandler

try:
    _meta = metadata("scrapy-stealth")
    __version__ = _meta["Version"]
    __author__ = _meta["Author-email"].split("<")[0].strip()
except PackageNotFoundError:
    __version__ = "unknown"
    __author__ = "Fawad Ali"

__license__ = "MIT"

__all__ = [
    # Middleware
    "StealthDownloaderMiddleware",
    # Engines
    "BaseEngine",
    # Strategies
    "ProxyRotator",
    "ProfileRotator",
    "RetryHandler",
    # Detectors
    "AntiBotDetector",
    # Config
    "StealthConfig",
    "config",
    # Exceptions
    "StealthException",
    "EngineNotFound",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
