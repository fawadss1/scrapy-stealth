from __future__ import annotations

from wreq.emulation import Emulation, Profile

from ..config import config
from .logger import get_logger

logger = get_logger()

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
    ("safari_ios",  "safari18_0_ios"),
    ("safari_ipad", "safari18_0_ios"),
    ("firefox",     "firefox135"),
    ("safari",      "safari18_0"),
    ("chrome",      "chrome131"),
    ("edge",        "chrome131"),
    ("opera",       "chrome131"),
    ("okhttp",      "chrome131"),
]


def _build_browser_map() -> dict[str, Profile]:
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


_BROWSER_MAP: dict[str, Profile] = _build_browser_map()


def _resolve_basic(profile: str | Profile) -> Profile:
    if isinstance(profile, Profile):
        return profile
    resolved = _BROWSER_MAP.get(profile)
    if resolved is None:
        logger.warning("Unknown browser profile %r, falling back to default", profile)
        return _BROWSER_MAP[config.get("DEFAULT_PROFILE")]
    return resolved


def _resolve_turbo(profile: str | Profile) -> str:
    name = profile if isinstance(profile, str) else config.get("DEFAULT_PROFILE")
    name_lower = name.lower()
    for prefix, target in _TURBO_PREFIXES:
        if prefix in name_lower:
            return target
    logger.warning("Unknown browser profile %r for turbo driver, using chrome131", name)
    return "chrome131"


def resolve_browser(profile: str | Profile, backend: str = "basic") -> Profile | str:
    if backend == "turbo":
        return _resolve_turbo(profile)
    return _resolve_basic(profile)
