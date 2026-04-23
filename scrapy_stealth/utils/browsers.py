from __future__ import annotations

import rnet

from ..constants import DEFAULT_IMPERSONATE
from .logger import get_logger

logger = get_logger()

_BROWSER_MAP: dict[str, rnet.Impersonate] = {
    # Chrome
    "chrome_120": rnet.Impersonate.Chrome120,
    "chrome_123": rnet.Impersonate.Chrome123,
    "chrome_124": rnet.Impersonate.Chrome124,
    "chrome_126": rnet.Impersonate.Chrome126,
    "chrome_127": rnet.Impersonate.Chrome127,
    "chrome_128": rnet.Impersonate.Chrome128,
    "chrome_129": rnet.Impersonate.Chrome129,
    "chrome_130": rnet.Impersonate.Chrome130,
    "chrome_131": rnet.Impersonate.Chrome131,
    "chrome_132": rnet.Impersonate.Chrome132,
    "chrome_133": rnet.Impersonate.Chrome133,
    "chrome_134": rnet.Impersonate.Chrome134,
    "chrome_135": rnet.Impersonate.Chrome135,
    "chrome_136": rnet.Impersonate.Chrome136,
    "chrome_137": rnet.Impersonate.Chrome137,
    # Firefox desktop
    "firefox_120": rnet.Impersonate.Firefox128,
    "firefox_128": rnet.Impersonate.Firefox128,
    "firefox_133": rnet.Impersonate.Firefox133,
    "firefox_135": rnet.Impersonate.Firefox135,
    "firefox_136": rnet.Impersonate.Firefox136,
    "firefox_139": rnet.Impersonate.Firefox139,
    # Firefox private/incognito mode
    "firefox_private_135": rnet.Impersonate.FirefoxPrivate135,
    "firefox_private_136": rnet.Impersonate.FirefoxPrivate136,
    # Firefox mobile
    "firefox_android_135": rnet.Impersonate.FirefoxAndroid135,
    # Safari macOS
    "safari_17": rnet.Impersonate.Safari17_5,
    "safari_17_5": rnet.Impersonate.Safari17_5,
    "safari_18": rnet.Impersonate.Safari18,
    "safari_18_2": rnet.Impersonate.Safari18_2,
    "safari_18_3": rnet.Impersonate.Safari18_3,
    "safari_18_3_1": rnet.Impersonate.Safari18_3_1,
    "safari_18_5": rnet.Impersonate.Safari18_5,
    # Safari iOS
    "safari_ios_16_5": rnet.Impersonate.SafariIos16_5,
    "safari_ios_17_2": rnet.Impersonate.SafariIos17_2,
    "safari_ios_17_4_1": rnet.Impersonate.SafariIos17_4_1,
    "safari_ios_18_1_1": rnet.Impersonate.SafariIos18_1_1,
    # Safari iPadOS
    "safari_ipad_18": rnet.Impersonate.SafariIPad18,
    # Edge
    "edge_122": rnet.Impersonate.Edge122,
    "edge_127": rnet.Impersonate.Edge127,
    "edge_131": rnet.Impersonate.Edge131,
    "edge_134": rnet.Impersonate.Edge134,
    # Opera
    "opera_116": rnet.Impersonate.Opera116,
    "opera_117": rnet.Impersonate.Opera117,
    "opera_118": rnet.Impersonate.Opera118,
    "opera_119": rnet.Impersonate.Opera119,
    # OkHttp — Android app HTTP client fingerprints
    "okhttp_3_9": rnet.Impersonate.OkHttp3_9,
    "okhttp_3_11": rnet.Impersonate.OkHttp3_11,
    "okhttp_3_13": rnet.Impersonate.OkHttp3_13,
    "okhttp_3_14": rnet.Impersonate.OkHttp3_14,
    "okhttp_4_9": rnet.Impersonate.OkHttp4_9,
    "okhttp_4_10": rnet.Impersonate.OkHttp4_10,
    "okhttp_4_12": rnet.Impersonate.OkHttp4_12,
    "okhttp_5": rnet.Impersonate.OkHttp5,
}


def resolve_browser(value: str | rnet.Impersonate | None) -> rnet.Impersonate:
    if isinstance(value, rnet.Impersonate):
        return value
    name: str = value if isinstance(value, str) else DEFAULT_IMPERSONATE
    resolved = _BROWSER_MAP.get(name)
    if resolved is None:
        logger.warning("Unknown browser %r, falling back to default", name)
        return _BROWSER_MAP[DEFAULT_IMPERSONATE]
    return resolved
