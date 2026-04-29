from __future__ import annotations

_CHROMIUM: dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

_FIREFOX: dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Connection": "keep-alive",
}

# Safari does NOT send Sec-Fetch-* or sec-ch-ua headers — including them breaks the fingerprint
_SAFARI: dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Upgrade-Insecure-Requests": "1",
}

# OkHttp is a minimal Android HTTP client — extra headers would look suspicious
_OKHTTP: dict[str, str] = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip",
    "Connection": "keep-alive",
}

_FAMILY: dict[str, dict[str, str]] = {
    "chrome": _CHROMIUM,
    "edge": _CHROMIUM,
    "opera": _CHROMIUM,
    "firefox": _FIREFOX,
    "safari": _SAFARI,
    "okhttp": _OKHTTP,
}

# Brand name per Chromium-based family used in sec-ch-ua
_CH_BRAND: dict[str, str] = {
    "chrome": "Google Chrome",
    "edge": "Microsoft Edge",
    "opera": "Opera",
}

# Headers controlled by browser impersonation — Scrapy defaults must never override these.
# User-Agent is always stripped: rnet sets the correct browser UA via impersonation.
_FINGERPRINT_KEYS: frozenset[str] = frozenset({
    "user-agent",
    "accept",
    "accept-language",
    "accept-encoding",
    "sec-fetch-dest",
    "sec-fetch-mode",
    "sec-fetch-site",
    "sec-fetch-user",
    "sec-ch-ua",
    "sec-ch-ua-mobile",
    "sec-ch-ua-platform",
    "upgrade-insecure-requests",
    "cache-control",
    "connection",
})


def _chromium_version(profile: str) -> str:
    for part in reversed(profile.split("_")):
        if part.isdigit():
            return part
    return "137"


def _ch_ua_headers(profile: str, family: str) -> dict[str, str]:
    brand = _CH_BRAND.get(family, "Google Chrome")
    version = _chromium_version(profile)
    return {
        "sec-ch-ua": f'"{brand}";v="{version}", "Chromium";v="{version}", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }


def get_default_headers(profile: str) -> dict[str, str]:
    for family, headers in _FAMILY.items():
        if profile.startswith(family):
            hdrs = dict(headers)
            if family in _CH_BRAND:
                hdrs.update(_ch_ua_headers(profile, family))
            return hdrs
    hdrs = dict(_CHROMIUM)
    hdrs.update(_ch_ua_headers(profile, "chrome"))
    return hdrs


def merge_headers(defaults: dict[str, str], request_headers: dict[str, str]) -> dict[str, str]:
    # Keep only non-fingerprint request headers (Cookie, Authorization, custom headers).
    # Fingerprint headers always use browser defaults so the profile stays consistent.
    custom = {k: v for k, v in request_headers.items() if k.lower() not in _FINGERPRINT_KEYS}
    return {**defaults, **custom}
