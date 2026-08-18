from __future__ import annotations

from datetime import timedelta
from typing import Any

from scrapy.http import Request, Response

from ..exceptions import StealthDependencyError

try:
    from wreq.blocking import Client
    from wreq.proxy import Proxy
except ImportError as exc:
    StealthDependencyError.check("wreq", exc)

from ..config import config
from ..detectors.antibot import AntiBotDetector
from ..exceptions import (
    StealthConnectionError,
    StealthRequestError,
    StealthTimeoutError,
    raise_stealth,
)
from ..utils.browser.session import BanStreakTracker, SessionCache
from ..utils.core.console import console
from ..utils.core.logger import get_logger
from ..utils.core.response import StealthResponse
from ..utils.engine.profiles import resolve_browser
from ..utils.network.dns import (
    build_wreq_dns_options,
    dns_fingerprint,
    resolve_dns_overrides,
)
from ..utils.network.request import build_stealth_request
from .base import BaseEngine

logger = get_logger()

# Client cache key: (http2, frozen host→IP pairs).
# dns_options= on get()/post() is ignored.
_BasicClientKey = tuple[bool, tuple[tuple[str, str], ...]]


class BasicEngine(BaseEngine):
    """Stealth HTTP engine with browser profile impersonation (basic driver)."""

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        super().__init__(profile, timeout)
        self.default_profile = resolve_browser(self._default_profile)
        self._clients: SessionCache[_BasicClientKey, Client] = SessionCache(
            self._make_client
        )
        self._bans = BanStreakTracker()

    @property
    def driver_name(self) -> str:
        return "basic"

    @staticmethod
    def _make_client(key: _BasicClientKey) -> Client:
        http2, dns_items = key
        kwargs: dict[str, Any] = {"http2_only": http2}
        if dns_options := build_wreq_dns_options(dict(dns_items)):
            kwargs["dns_options"] = dns_options
        return Client(**kwargs)

    def _maybe_recycle_sessions(
        self, response: Response | None, current_proxy: str | None = None
    ) -> None:
        """Drop cached clients; rotate profile + proxy after N consecutive bans."""
        banned = response is not None and AntiBotDetector.is_browser_session_ban(
            response
        )
        should_recycle = self._bans.record(banned)
        self._record_response(response, banned)
        if not should_recycle:
            return
        profile, proxy = self._recycle_identity(current_proxy=current_proxy)
        self.default_profile = resolve_browser(profile)
        console.info(
            f"Recycling basic sessions after "
            f"{config.get('STEALTH_RECYCLE_AFTER_BANS')} consecutive bans "
            f"(profile={profile!r} proxy={proxy!r})"
        )
        self._bans.acknowledge_restart()
        self._clients.clear_all()
        self._record_recycle(profile, proxy)

    def _execute(self, request: Request) -> Response | None:
        ctx = self._ctx(request)
        self._record_request_identity(ctx.profile, ctx.proxy)
        try:
            emulation = (
                self.default_profile
                if ctx.profile == self._default_profile
                else resolve_browser(ctx.profile)
            )
            prepared = build_stealth_request(request, profile=ctx.profile)

            kwargs: dict[str, Any] = {
                "emulation": emulation,
                "timeout": timedelta(seconds=ctx.timeout),
                **prepared.basic_http_kwargs(),
            }
            if ctx.proxy:
                kwargs["proxy"] = Proxy.all(ctx.proxy)

            dns_overrides = resolve_dns_overrides(request)
            self._record_dns(len(dns_overrides))
            dns_key = dns_fingerprint(dns_overrides)
            if dns_key:
                logger.debug(
                    "Basic engine DNS override(s): %s",
                    dns_overrides,
                )

            logger.debug(
                "Initializing basic stealth client (profile=%s & protocol=%s)",
                ctx.profile,
                "HTTP/2" if ctx.http2 else "HTTP/1.1",
            )

            method_fn = getattr(
                self._clients.get((ctx.http2, dns_key)), prepared.method_name
            )
            resp = method_fn(prepared.url, **kwargs)

            body = resp.bytes()
            if AntiBotDetector.is_js_challenge_body(body.decode(errors="replace")):
                console.warning(
                    f"JS challenge detected at {request.url!r} — "
                    "switch to driver='browser' to bypass it."
                )

            response = StealthResponse(
                request=request,
                status=resp.status.as_int(),
                headers=resp.headers,
                body=body,
                _flags=["basic"],
            )
            self._maybe_recycle_sessions(response, current_proxy=ctx.proxy)
            return response

        except StealthRequestError as exc:
            logger.error("Basic engine invalid request: %s", exc)
            return None
        except TimeoutError:
            raise
        except Exception as exc:
            from wreq.exceptions import ConnectionError as WConn
            from wreq.exceptions import ProxyConnectionError as WProxyConn
            from wreq.exceptions import TimeoutError as WTimeout

            if isinstance(exc, WTimeout):
                raise_stealth(
                    StealthTimeoutError,
                    f"Basic engine timed out after {ctx.timeout}s fetching {request.url!r}",
                )
            if isinstance(exc, (WConn, WProxyConn)):
                raise_stealth(
                    StealthConnectionError,
                    f"Basic engine connection failed fetching {request.url!r}: {exc}",
                )
            logger.error("Basic engine request failed: %s", exc)
            return None
