from __future__ import annotations

from ..exceptions import StealthDependencyError

try:
    from wreq.emulation import Emulation, Profile

    _WREQ_AVAILABLE = True
    _wreq_import_error: ImportError | None = None
except ImportError as _wreq_err:
    _WREQ_AVAILABLE = False
    _wreq_import_error = _wreq_err
    Emulation = None  # type: ignore[assignment]
    Profile = None  # type: ignore[assignment]

from ..config import config
from .console import console

# Order matters: longer/more-specific prefixes must come before shorter ones.
_PREFIXES: list[tuple[str, str]] = [
    ("FirefoxPrivate", "firefox_private"),
    ("FirefoxAndroid", "firefox_android"),
    ("SafariIos", "safari_ios"),
    ("SafariIPad", "safari_ipad"),
    ("Safari", "safari"),
    ("Firefox", "firefox"),
    ("Chrome", "chrome"),
    ("Edge", "edge"),
    ("Opera", "opera"),
    ("OkHttp", "okhttp"),
]

_ALIASES: dict[str, str] = {
    "firefox_120": "firefox_128",
    "safari_17": "safari_17_5",
}

# Turbo driver browser targets, ordered most-specific first.
_TURBO_PREFIXES: list[tuple[str, str]] = [
    ("safari_ios", "safari18_0_ios"),
    ("safari_ipad", "safari18_0_ios"),
    ("firefox", "firefox135"),
    ("safari", "safari18_0"),
    ("chrome", "chrome131"),
    ("edge", "chrome131"),
    ("opera", "chrome131"),
    ("okhttp", "chrome131"),
]


def _require_wreq() -> None:
    """Raise StealthDependencyError if wreq failed to load."""
    if not _WREQ_AVAILABLE:
        StealthDependencyError.check("wreq", _wreq_import_error)


def _build_browser_map() -> dict[str, "Profile"]:
    if not _WREQ_AVAILABLE:
        return {}
    result: dict[str, Profile] = {}
    for attr in dir(Emulation):
        if attr.startswith("_"):
            continue
        value = getattr(Emulation, attr)
        if not isinstance(value, Profile):
            continue
        for prefix, key_prefix in _PREFIXES:
            if attr.startswith(prefix):
                version = attr[len(prefix):]
                result[f"{key_prefix}_{version.lower()}"] = value
                break
    for alias, target in _ALIASES.items():
        if target in result:
            result.setdefault(alias, result[target])
    return result


_BROWSER_MAP: dict[str, "Profile"] = _build_browser_map()


def _resolve_basic(profile: "str | Profile") -> "Profile":
    _require_wreq()
    if isinstance(profile, Profile):
        return profile
    resolved = _BROWSER_MAP.get(profile)
    if resolved is None:
        _default_profile = config.get("DEFAULT_PROFILE")
        console.warning(
            f"Unknown browser profile {profile!r}. Falling back to {_default_profile!r}"
        )
        return _BROWSER_MAP[_default_profile]
    return resolved


def _resolve_turbo(profile: "str | Profile") -> str:
    name = profile if isinstance(profile, str) else config.get("DEFAULT_PROFILE")
    name_lower = name.lower()
    for prefix, target in _TURBO_PREFIXES:
        if prefix in name_lower:
            return target
    console.warning(
        f"Unknown browser profile {name!r} for turbo driver, using chrome131"
    )
    return "chrome131"


def resolve_browser(profile: "str | Profile", backend: str = "basic") -> "Profile | str":
    if backend == "turbo":
        return _resolve_turbo(profile)
    return _resolve_basic(profile)
