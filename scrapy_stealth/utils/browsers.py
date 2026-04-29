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


def resolve_browser(value: str | Profile | None) -> Profile:
    if isinstance(value, Profile):
        return value
    name: str = value if isinstance(value, str) else config.get("DEFAULT_PROFILE")
    resolved = _BROWSER_MAP.get(name)
    if resolved is None:
        logger.warning("Unknown browser %r, falling back to default", name)
        return _BROWSER_MAP[config.get("DEFAULT_PROFILE")]
    return resolved
