from __future__ import annotations

import json
import threading
import urllib.request
from typing import Any

from packaging.version import Version

from ..core.meta_info import _pkg_meta

_lock = threading.Lock()
_update_check_started = False


def _installed_version() -> str:
    return _pkg_meta.version or "0.0.0"


def pypi_release_url(version: str, package: str | None = None) -> str:
    """PyPI release page for a specific package version."""
    name = package or _pkg_meta.name
    return f"https://pypi.org/project/{name}/{version}/"


def latest_pypi_release(package: str | None = None) -> dict[str, Any]:
    """Return PyPI project JSON for *package* (defaults to this distribution)."""
    name = package or _pkg_meta.name
    url = f"https://pypi.org/pypi/{name}/json"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{_pkg_meta.name}/{_installed_version()} update-check",
        },
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.loads(response.read().decode())


def get_update_url(
    current_version: str | None = None,
    *,
    silent_fail: bool = True,
    package: str | None = None,
) -> str | None:
    """
    Return the PyPI release URL when a newer version exists, otherwise ``None``.

    Network and parse errors are swallowed when *silent_fail* is ``True`` so
    update checks never interfere with crawling.
    """
    try:
        pypi_data = latest_pypi_release(package)
        latest_version = str(pypi_data["info"]["version"])
        latest = Version(latest_version.lstrip("v"))
        used = Version((current_version or _installed_version()).lstrip("v"))
        if used >= latest:
            return None
        return pypi_release_url(latest_version, package)
    except Exception:
        if not silent_fail:
            raise
        return None


def _notify_if_update_available() -> None:
    from ..core.console import console

    if url := get_update_url():
        console.info(
            f"A newer version of {_pkg_meta.name} is available. "
            f"Update with `pip install -U {_pkg_meta.name}` or see {url}"
        )


def update_available() -> None:
    """Check PyPI once per process in a background thread and notify if needed."""
    global _update_check_started

    with _lock:
        if _update_check_started:
            return
        _update_check_started = True

    threading.Thread(
        target=_notify_if_update_available,
        daemon=True,
        name="scrapy-stealth-update-check",
    ).start()


def _reset_update_check_state() -> None:
    """Test helper — allow another update check in the same process."""
    global _update_check_started
    with _lock:
        _update_check_started = False
