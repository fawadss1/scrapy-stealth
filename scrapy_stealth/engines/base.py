from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from scrapy.http import Response, Request


class BaseEngine(ABC):
    """Abstract base class for all stealth engines."""

    @abstractmethod
    def fetch(self, request: Request, spider: Any) -> Response | None:
        """Fetch a request and return a Scrapy Response or None."""
        raise NotImplementedError
