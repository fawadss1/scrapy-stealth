from __future__ import annotations

try:
    from scrapy.exceptions import DownloadTimeoutError as _DownloadTimeoutError
except ImportError:
    _DownloadTimeoutError = TimeoutError


class StealthException(Exception):
    """Base exception for scrapy-stealth."""


class EngineNotFound(StealthException):
    """Raised when engine is not registered."""


class StealthTimeoutError(StealthException, _DownloadTimeoutError):
    """Raised when a stealth engine request times out."""


class StealthConnectionError(StealthException, ConnectionError):
    """Raised when a stealth engine fails to connect (DNS, network, proxy)."""


class StealthBrowserNotFoundError(StealthException):
    """Raised when the browser binary is not found on the system."""


class StealthDependencyError(StealthException, ImportError):
    """
    Raised when a compiled optional dependency fails to import.

    This typically means a required native library (DLL / .so) could not be
    loaded.  On Windows the most common cause is a missing Visual C++
    Redistributable; on Linux it is usually a missing system library.

    Use :meth:`check` at the top of any module that wraps a compiled import so
    the error surface is consistent across the whole package:

    .. code-block:: python

        try:
            from wreq.blocking import Client
        except ImportError as exc:
            StealthDependencyError.check("wreq", exc)
    """

    _WINDOWS_HINT = (
        "On Windows this is almost always caused by a missing Visual C++ Runtime.\n"
        "Install BOTH redistributables below and restart your terminal:\n"
        "  x64 → https://aka.ms/vs/17/release/vc_redist.x64.exe\n"
        "  x86 → https://aka.ms/vs/17/release/vc_redist.x86.exe"
    )

    _LINUX_HINT = (
        "On Linux, ensure the required system libraries are installed.\n"
        "Try: sudo apt-get install libssl-dev libcurl4-openssl-dev  (Debian/Ubuntu)\n"
        "  or: sudo yum install openssl-devel libcurl-devel          (RHEL/CentOS)"
    )

    def __init__(self, package: str, cause: BaseException) -> None:
        import sys

        platform_hint = (
            self._WINDOWS_HINT if sys.platform == "win32" else self._LINUX_HINT
        )
        message = (
            f"\n\n[scrapy-stealth] Failed to import '{package}' — a compiled dependency.\n"
            f"{platform_hint}\n"
            f"Original error: {cause}"
        )
        super().__init__(message)
        self.package = package
        self.cause = cause

    @classmethod
    def check(cls, package: str, exc: BaseException) -> None:
        """
        Re-raise *exc* as a :class:`StealthDependencyError`.

        Call this inside an ``except ImportError`` block at module level so
        every compiled-dependency failure produces a uniform, actionable error.

        :param package: The pip package name that failed to import.
        :param exc:     The original :class:`ImportError` caught.
        :raises StealthDependencyError: Always.
        """
        raise cls(package, exc) from exc
