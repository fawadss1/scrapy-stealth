from __future__ import annotations

from typing import Any

from scrapy.http import Request, Response

from ..exceptions import StealthDependencyError

try:
    from curl_cffi import CurlHttpVersion, CurlOpt
    from curl_cffi.requests import Session
except ImportError as exc:
    StealthDependencyError.check("curl_cffi", exc)

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
from ..utils.network.dns import build_curl_resolve, resolve_dns_overrides
from ..utils.network.request import build_stealth_request
from .base import BaseEngine

logger = get_logger()

_TurboSessionKey = tuple[Any, tuple[str, ...]]


class TurboEngine(BaseEngine):
    """Stealth HTTP engine with deep TLS fingerprinting (turbo driver)."""

    def __init__(self, profile: str | None = None, timeout: int | None = None) -> None:
        super().__init__(profile, timeout)
        self._sessions: SessionCache[_TurboSessionKey, Session] = SessionCache(
            self._make_session
        )
        self._bans = BanStreakTracker()

    @property
    def driver_name(self) -> str:
        return "turbo"

    @staticmethod
    def _make_session(key: _TurboSessionKey) -> Session:
        impersonate, resolve_entries = key
        kwargs: dict[str, Any] = {"impersonate": impersonate, "default_headers": True}
        if resolve_entries:
            kwargs["curl_options"] = {CurlOpt.RESOLVE: list(resolve_entries)}
        return Session(**kwargs)

    def _maybe_recycle_sessions(
        self, response: Response | None, current_proxy: str | None = None
    ) -> None:
        """Drop cached sessions; rotate profile + proxy after N consecutive bans."""
        banned = response is not None and AntiBotDetector.is_browser_session_ban(
            response
        )
        should_recycle = self._bans.record(banned)
        self._record_response(response, banned)
        if not should_recycle:
            return
        profile, proxy = self._recycle_identity(current_proxy=current_proxy)
        console.info(
            f"Recycling turbo sessions after "
            f"{config.get('STEALTH_RECYCLE_AFTER_BANS')} consecutive bans "
            f"(profile={profile!r} proxy={proxy!r})"
        )
        self._bans.acknowledge_restart()
        self._sessions.clear_all()
        self._record_recycle(profile, proxy)

    def _execute(self, request: Request) -> Response | None:
        ctx = self._ctx(request)
        self._record_request_identity(ctx.profile, ctx.proxy)
        try:
            browser = resolve_browser(ctx.profile, backend="turbo", http3=ctx.http3)
            prepared = build_stealth_request(request)
            if ctx.http3:
                http_version = CurlHttpVersion.V3
            elif ctx.http2:
                http_version = CurlHttpVersion.V2_0
            else:
                http_version = CurlHttpVersion.V1_1

            dns_overrides = resolve_dns_overrides(request)
            self._record_dns(len(dns_overrides))
            resolve_entries = tuple(build_curl_resolve(dns_overrides, request.url))
            if resolve_entries:
                logger.debug("Turbo engine DNS override(s): %s", dns_overrides)

            logger.debug(
                "Initializing turbo stealth client (profile=%s impersonate=%s http=%s)",
                ctx.profile,
                browser,
                http_version.name,
            )

            session = self._sessions.get((browser, resolve_entries))
            resp = getattr(session, prepared.method_name)(
                prepared.url,
                **prepared.turbo_kwargs(
                    timeout=ctx.timeout,
                    http_version=http_version,
                    proxy=ctx.proxy,
                ),
            )

            resp_headers = {
                k: v for k, v in resp.headers.items() if k.lower() != "content-encoding"
            }
            if AntiBotDetector.is_js_challenge_body(
                resp.content.decode(errors="replace")
            ):
                console.warning(
                    f"JS challenge detected at {request.url!r} — "
                    "switch to driver='browser' to bypass it."
                )

            response = StealthResponse(
                request=request,
                status=resp.status_code,
                headers=resp_headers,
                body=resp.content,
                encoding=resp.encoding,
                _flags=["turbo"],
            )
            self._maybe_recycle_sessions(response, current_proxy=ctx.proxy)
            return response

        except StealthRequestError as exc:
            logger.error("Turbo engine invalid request: %s", exc)
            return None
        except TimeoutError:
            raise
        except Exception as exc:
            from curl_cffi.requests.exceptions import ConnectionError as CurlConn
            from curl_cffi.requests.exceptions import DNSError as CurlDNS
            from curl_cffi.requests.exceptions import ProxyError as CurlProxy
            from curl_cffi.requests.exceptions import Timeout as CurlTimeout

            if isinstance(exc, CurlTimeout):
                raise_stealth(
                    StealthTimeoutError,
                    f"Turbo engine timed out after {ctx.timeout}s fetching {request.url!r}",
                )
            if isinstance(exc, (CurlConn, CurlDNS, CurlProxy)):
                raise_stealth(
                    StealthConnectionError,
                    f"Turbo engine connection failed fetching {request.url!r}: {exc}",
                )
            logger.error("Turbo engine request failed: %s", exc)
            return None
