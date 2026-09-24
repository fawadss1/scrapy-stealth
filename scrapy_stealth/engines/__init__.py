from typing import TYPE_CHECKING

from .base import BaseEngine
from .scrapy import ScrapyEngine

if TYPE_CHECKING:
    from .basic import BasicEngine
    from .browser import BrowserEngine
    from .turbo import TurboEngine

__all__ = [
    "BaseEngine",
    "ScrapyEngine",
    "BasicEngine",
    "TurboEngine",
    "BrowserEngine",
]


def __getattr__(name: str) -> object:
    if name == "BasicEngine":
        from .basic import BasicEngine

        return BasicEngine
    if name == "TurboEngine":
        from .turbo import TurboEngine

        return TurboEngine
    if name == "BrowserEngine":
        from .browser import BrowserEngine

        return BrowserEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
