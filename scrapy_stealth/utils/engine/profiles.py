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

_H3_PRESETS = frozenset(
    {
        "chrome145",
        "chrome146",
        "chrome150",
        "chrome151",
        "chrome152",
        "firefox147",
        "firefox153",
        "firefox154",
        "firefox155",
    }
)
_DEFAULT_TURBO = "chrome152"

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
    ("safari_ios", "safari270_ios"),
    ("safari_ipad", "safari270_ios"),
    ("firefox", "firefox155"),
    ("safari", "safari270"),
    ("chrome", "chrome152"),
    ("edge", "chrome152"),
    ("opera", "chrome152"),
    ("okhttp", "chrome152"),
]


def _require_wreq() -> None:
    """Raise StealthDependencyError if the basic driver HTTP client failed to load."""
    if not _WREQ_AVAILABLE:
        err = _wreq_import_error or ImportError("basic driver HTTP client is missing")
        StealthDependencyError.check("basic driver", err)


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
        return "chrome152"
    if target.startswith("firefox"):
        return "firefox155"
    return target


def _resolve_basic(profile: str | Profile) -> Profile:
    _require_wreq()
    if not isinstance(profile, str):
        return profile
    if profile in _BROWSER_MAP:
        return _BROWSER_MAP[profile]
    for name in (ProfileRotator.get(), "chrome_154", "chrome_152", "chrome_150"):
        if name in _BROWSER_MAP:
            return _BROWSER_MAP[name]
    return next(iter(_BROWSER_MAP.values()))


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
