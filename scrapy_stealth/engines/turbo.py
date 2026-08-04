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
from ..exceptions import StealthConnectionError, StealthTimeoutError, raise_stealth
from ..utils.console import console
from ..utils.dns import build_curl_resolve, resolve_dns_overrides
from ..utils.headers import _FINGERPRINT_KEYS
from ..utils.logger import get_logger
from ..utils.profiles import resolve_browser
from ..utils.response import StealthResponse
from ..utils.session import BanStreakTracker, SessionCache
from .base import BaseEngine

logger = get_logger()

# Session cache key: (impersonate profile, frozen sorted DNS resolve entries).
# DNS is applied at Session construction via CurlOpt.RESOLVE (curl_cffi does not
# accept per-request curl_options on Session.request).
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
        kwargs: dict[str, Any] = {"impersonate": impersonate}
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
            browser = resolve_browser(ctx.profile, backend="turbo")

            headers = {
                k: v
                for k, v in request.headers.to_unicode_dict().items()
                if k.lower() not in _FINGERPRINT_KEYS
            }

            kwargs: dict[str, Any] = {
                "headers": headers,
                "timeout": ctx.timeout,
                "http_version": CurlHttpVersion.V2_0
                if ctx.http2
                else CurlHttpVersion.V1_1,
            }
            if request.body:
                kwargs["data"] = request.body
            if ctx.proxy:
                kwargs["proxies"] = {"http": ctx.proxy, "https": ctx.proxy}

            dns_overrides = resolve_dns_overrides(request)
            self._record_dns(len(dns_overrides))
            resolve_entries = tuple(build_curl_resolve(dns_overrides, request.url))
            if resolve_entries:
                logger.debug(
                    "Turbo engine DNS override(s): %s",
                    dns_overrides,
                )

            logger.debug(
                "Initializing turbo stealth client (profile=%s & protocol=%s)",
                ctx.profile,
                "HTTP/2" if ctx.http2 else "HTTP/1.1",
            )

            session = self._sessions.get((browser, resolve_entries))
            method_fn = getattr(session, request.method.lower())
            resp = method_fn(request.url, **kwargs)

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
                    f"Turbo engine connection failed fetching {request.url!r}",
                )
            logger.error("Turbo engine request failed: %s", exc)
            return None
