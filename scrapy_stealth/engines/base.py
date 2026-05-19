from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from scrapy.http import Request, Response

from ..config import config
from ..utils.meta import _get_meta_data

_T = TypeVar("_T")


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

    async def fetch(self, request: Request, spider: Any) -> Response | None:
        """
        This method processes the given request by delegating its execution to a worker
        thread. It ensures asynchronous execution and returns the result as a Response
        or None.

        Args:
            request (Request): The request object to be processed.
            spider (Any): The spider instance associated with this request.

        Returns:
            Response | None: The result of processing the request. Computation is
            completed asynchronously via asyncio's thread-pool executor.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._execute_timed, request)

    def _execute_timed(self, request: Request) -> Response | None:
        resp, latency = self._timed(self._execute, request)
        if resp is not None:
            resp.meta["download_latency"] = latency
        return resp

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

    @staticmethod
    def _timed(
            fn: Callable[..., _T],
            *args: Any,
            **kwargs: Any
    ) -> tuple[_T, float]:
        """
        Executes the provided function and measures the time taken for its execution.

        This static method is used to time the execution of a function. It calculates
        and returns the result of the function along with the time it takes to execute
        in seconds.

        Returns:
        tuple[_T, float]
            A tuple containing the result of the function execution and the elapsed
            time in seconds.
        """
        start = time.time()
        result = fn(*args, **kwargs)
        return result, time.time() - start

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
