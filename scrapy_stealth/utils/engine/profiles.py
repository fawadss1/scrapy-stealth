from __future__ import annotations

from typing import TYPE_CHECKING

from ...exceptions import StealthDependencyError

if TYPE_CHECKING:
    from wreq.emulation import Profile

try:
    from wreq.emulation import Emulation
    from wreq.emulation import Profile as _ProfileCls

    _WREQ_AVAILABLE = True
    _wreq_import_error: ImportError | None = None
except ImportError as _wreq_err:
    _WREQ_AVAILABLE = False
    _wreq_import_error = _wreq_err
    Emulation = None  # type: ignore[misc, assignment]
    _ProfileCls = type("_ProfileCls", (), {})

from ...strategies.fingerprint import ProfileRotator

_H3_PRESETS = frozenset({"chrome145", "chrome146", "chrome150", "firefox147"})
_DEFAULT_TURBO = "chrome150"

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
    ("chrome", "chrome150"),
    ("edge", "chrome150"),
    ("opera", "chrome150"),
    ("okhttp", "chrome150"),
]


def _require_wreq() -> None:
    """Raise StealthDependencyError if wreq failed to load."""
    if not _WREQ_AVAILABLE:
        err = _wreq_import_error or ImportError("wreq library is missing")
        StealthDependencyError.check("wreq", err)


def _build_browser_map() -> dict[str, Profile]:
    if not _WREQ_AVAILABLE:
        return {}
    result: dict[str, Profile] = {}
    for attr in dir(Emulation):
        if attr.startswith("_"):
            continue
        value = getattr(Emulation, attr)
        if not isinstance(value, _ProfileCls):
            continue
        for prefix, key_prefix in _PREFIXES:
            if attr.startswith(prefix):
                version = attr[len(prefix) :]
                result[f"{key_prefix}_{version.lower()}"] = value
                break
    for alias, target in _ALIASES.items():
        if target in result:
            result.setdefault(alias, result[target])
    return result


_BROWSER_MAP: dict[str, Profile] = _build_browser_map()


def _profile_name(profile: str | Profile) -> str:
    return profile if isinstance(profile, str) else ProfileRotator.get()


def _turbo_target(name: str) -> str:
    name_lower = name.lower()
    for prefix, target in _TURBO_PREFIXES:
        if prefix in name_lower:
            return target
    return _DEFAULT_TURBO


def _h3_target(target: str) -> str:
    if target in _H3_PRESETS:
        return target
    if target.startswith("chrome"):
        return "chrome150"
    if target.startswith("firefox"):
        return "firefox147"
    return target


def _resolve_basic(profile: str | Profile) -> Profile:
    _require_wreq()
    if not isinstance(profile, str):
        return profile
    return _BROWSER_MAP.get(profile) or _BROWSER_MAP[ProfileRotator.get()]


def _resolve_turbo(profile: str | Profile, *, http3: bool = False) -> str:
    target = _turbo_target(_profile_name(profile))
    return _h3_target(target) if http3 else target


def resolve_browser(
    profile: str | Profile,
    backend: str = "basic",
    *,
    http3: bool = False,
) -> Profile | str:
    if backend == "turbo":
        return _resolve_turbo(profile, http3=http3)
    return _resolve_basic(profile)
