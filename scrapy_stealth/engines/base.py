from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    TypeVar,
    cast,
)

from scrapy.http import Request, Response

from ..config import config
from ..strategies.fingerprint import ProfileRotator
from ..utils.core.meta import _get_meta_data
from ..utils.telemetry.stats import StealthStats

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
        http3 (bool): When True, prefer HTTP/3 (QUIC) on the turbo driver.
    """

    profile: str
    proxy: str | None
    timeout: int | float
    http2: bool
    http3: bool


class BaseEngine(ABC):
    """
    Base class for implementing an engine that processes requests and executes them in an
    asynchronous context.

    This abstract base class provides a common interface and functionality for handling
    requests, such as delegating their execution to worker threads and creating request
    contexts. Subclasses are required to override the `_execute` method to define their
    specific execution logic.
    """

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        self._default_profile: str = profile or ProfileRotator.get()
        self._default_proxy: str | None = None
        self.timeout: int = timeout or config.get("DEFAULT_TIMEOUT")
        self._stealth_stats = StealthStats()
        self.seed_proxy_from_config()

    @property
    def driver_name(self) -> str:
        """Stealth driver label used in Scrapy stats keys."""
        return "stealth"

    def set_stats(self, stats: Any | None) -> None:
        """Attach Scrapy's stats collector (or ``None`` to disable)."""
        self._stealth_stats = StealthStats(stats)

    def close(self) -> None:
        """Release engine resources. Override when the engine holds state."""

    def _record_identity(self, profile: str | None, proxy: str | None) -> None:
        self._stealth_stats.set("stealth/driver", self.driver_name)
        self._stealth_stats.set_profile(profile)
        self._stealth_stats.set_proxy(proxy)

    def _record_request_identity(self, profile: str | None, proxy: str | None) -> None:
        self._record_identity(profile, proxy)
        if proxy:
            self._stealth_stats.record_proxy_request(self.driver_name)

    def _record_response(self, response: Response | None, banned: bool) -> None:
        if response is None:
            return
        streak = getattr(self, "_bans", None)
        current_streak = streak.streak if streak is not None else 0
        self._stealth_stats.record_response(self.driver_name, response.status, banned)
        self._stealth_stats.record_ban(self.driver_name, current_streak, banned)

    def _record_dns(self, host_count: int) -> None:
        self._stealth_stats.record_dns(self.driver_name, host_count)

    def _record_recycle(self, profile: str | None, proxy: str | None) -> None:
        self._stealth_stats.record_recycle(self.driver_name)
        self._record_identity(profile, proxy)

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
            completed asynchronously in a thread pool.
        """
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._execute_timed, request)
        except RuntimeError:
            from twisted.internet.threads import deferToThread

            return await cast(
                Awaitable[Optional[Response]],
                deferToThread(self._execute_timed, request),
            )

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
            proxy=_get_meta_data(request, "proxy", self._default_proxy),
            timeout=_get_meta_data(request, "stealth_timeout", self.timeout),
            http2=_get_meta_data(request, "http2", config.get("HTTP2")),
            http3=_get_meta_data(request, "http3", config.get("HTTP3")),
        )

    def seed_proxy_from_config(self) -> None:
        """Set default proxy from ``STEALTH_PROXIES`` when none is chosen yet."""
        if self._default_proxy:
            return
        proxies = config.get("STEALTH_PROXIES") or []
        if not proxies:
            return
        from ..strategies.proxy import ProxyRotator

        self._default_proxy = ProxyRotator(proxies).get()

    def _rotate_default_profile(self) -> str:
        """Pick a new default fingerprint profile (prefer different from current)."""
        from ..strategies.fingerprint import ProfileRotator

        current = self._default_profile
        new = ProfileRotator.get()
        if new == current:
            for _ in range(5):
                candidate = ProfileRotator.get()
                if candidate != current:
                    new = candidate
                    break
        self._default_profile = new
        return new

    def _rotate_default_proxy(self) -> str | None:
        """Pick a new default proxy from ``STEALTH_PROXIES`` (prefer different).

        When the pool is empty, keep the current default (e.g. a per-request
        meta proxy remembered on recycle) — never wipe it to ``None``.
        """
        from ..strategies.proxy import ProxyRotator

        proxies = config.get("STEALTH_PROXIES") or []
        if not proxies:
            return self._default_proxy
        rotator = ProxyRotator(proxies)
        current = self._default_proxy
        new = rotator.get()
        if new == current and len(proxies) > 1:
            for _ in range(5):
                candidate = rotator.get()
                if candidate != current:
                    new = candidate
                    break
        self._default_proxy = new
        return new

    def _recycle_identity(
        self, current_proxy: str | None = None
    ) -> tuple[str, str | None]:
        """Rotate profile + proxy used after a ban-streak session recycle.

        ``current_proxy`` is the proxy from the request that hit the ban streak.
        If ``STEALTH_PROXIES`` is empty, that proxy is kept as the engine default
        so meta-only proxy setups are not cleared to ``None``.
        """
        proxies = config.get("STEALTH_PROXIES") or []
        if current_proxy and not proxies:
            self._default_proxy = current_proxy
        elif current_proxy and not self._default_proxy:
            self._default_proxy = current_proxy
        return self._rotate_default_profile(), self._rotate_default_proxy()

    @staticmethod
    def _timed(fn: Callable[..., _T], *args: Any, **kwargs: Any) -> tuple[_T, float]:
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
