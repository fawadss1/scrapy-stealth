from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from scrapy.http import Request, Response
from twisted.internet.defer import Deferred
from twisted.internet.threads import deferToThread

from ..config import config
from ..utils.meta import _get_meta_data


@dataclass(frozen=True)
class RequestContext:
    """
    Represents the contextual information required for making an HTTP request.

    Attributes:
        profile (str): The profile name associated with the request.
        proxy (str | None): The proxy address to be used for the request.
            If no proxy is required, this can be set to None.
        timeout (int | float): The maximum duration for the request to wait for
            a response, expressed in seconds.
        http2 (bool): Indicates whether the request should use HTTP/2 or not.
    """
    profile: str
    proxy: str | None
    timeout: int | float
    http2: bool


class BaseEngine(ABC):
    """
    Base class for implementing an engine that processes requests and executes them in an
    asynchronous context.

    This abstract base class provides a common interface and functionality for handling
    requests, such as delegating their execution to worker threads and creating request
    contexts. Subclasses are required to override the `_execute` method to define their
    specific execution logic.
    """

    def __init__(
            self,
            profile: str | None = None,
            timeout: int | None = None
    ) -> None:
        self._default_profile: str = profile or config.get("DEFAULT_PROFILE")
        self.timeout: int = timeout or config.get("DEFAULT_TIMEOUT")

    def fetch(self, request: Request, spider: Any) -> Response | Deferred | None:
        """
        This method processes the given request by delegating its execution to a worker
        thread. It ensures asynchronous execution and returns the result as a Response,
        a Deferred object, or None.

        Args:
            request (Request): The request object to be processed.
            spider (Any): The spider instance associated with this request.

        Returns:
            Response | Deferred | None: The result of processing the request. If deferred,
            the computation will be completed asynchronously.
        """
        return deferToThread(self._execute, request)

    def _ctx(self, request: Request) -> RequestContext:
        """
        Creates a RequestContext object initialized with metadata derived from the given request.

        Parameters:
        request (Request): The request object from which metadata will be retrieved.

        Returns:
        RequestContext: A context object with attributes populated based on the request metadata.
        """
        return RequestContext(
            profile=_get_meta_data(request, "profile", self._default_profile),
            proxy=_get_meta_data(request, "proxy"),
            timeout=_get_meta_data(request, "stealth_timeout", self.timeout),
            http2=_get_meta_data(request, "http2", config.get("HTTP2")),
        )

    @abstractmethod
    def _execute(self, request: Request) -> Response | None:
        """
        Represents an abstract method for executing a request, and it must be
        overridden in a subclass to provide specific functionality. This method
        acts as a contract enforcing the implementation in derived classes.

        Raises:
            NotImplementedError: If the method is called without being overridden
                by a subclass.
        """
        raise NotImplementedError
