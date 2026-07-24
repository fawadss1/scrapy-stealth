r"""
   _____                                  _____ __             ____  __
  / ___/______________ _____  __  __     / ___// /____  ____ _/ / /_/ /_
  \__ \/ ___/ ___/ __ `/ __ \/ / / /_____\__ \/ __/ _ \/ __ `/ / __/ __ \
 ___/ / /__/ /  / /_/ / /_/ / /_/ /_____/__/ / /_/  __/ /_/ / / /_/ / / /
/____/\___/_/   \__,_/ .___/\__, /     /____/\__/\___/\__,_/_/\__/_/ /_/
                    /_/    /____/

scrapy-stealth: A pluggable anti-bot and stealth framework for Scrapy.

Quick start
-----------
Add the middleware to your settings.py or spider custom_settings::

    DOWNLOADER_MIDDLEWARES = {
        "scrapy_stealth.StealthDownloaderMiddleware": 950,
    }

    # Optional: proxy list for automatic rotation
    STEALTH_PROXIES = [
        "http://proxy1:8080",
        "socks5://proxy2:1080",
    ]

Per-request usage via ``request.meta["stealth"]``::

    yield scrapy.Request(
        url,
        meta={"stealth": {}},  # activates stealth; profile/proxy rotate on ban recycle
    )

Optional: ``STEALTH_PROXIES`` in settings — first proxy is used automatically; a new
profile + proxy are chosen when the session recycles after consecutive bans.
Explicit ``meta["stealth"]["profile"]`` / ``["proxy"]`` always win.
"""

from .config import StealthConfig, config
from .detectors.antibot import AntiBotDetector
from .engines.base import BaseEngine
from .engines.basic import BasicEngine
from .engines.turbo import TurboEngine
from .exceptions import (
    EngineNotFound,
    StealthBrowserNotFoundError,
    StealthConnectionError,
    StealthException,
    StealthTimeoutError,
)
from .middlewares.stealth import StealthDownloaderMiddleware
from .strategies.fingerprint import ProfileRotator
from .strategies.proxy import ProxyRotator
from .strategies.retry import RetryHandler
from .utils.meta_info import _pkg_meta

__version__: str = _pkg_meta.version
__author__: str = _pkg_meta.author
__license__: str = _pkg_meta.license

__all__ = [
    # Middleware
    "StealthDownloaderMiddleware",
    # Engines
    "BaseEngine",
    "BasicEngine",
    "TurboEngine",
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
    "StealthTimeoutError",
    "StealthConnectionError",
    "StealthBrowserNotFoundError",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
