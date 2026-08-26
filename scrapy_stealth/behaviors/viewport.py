from __future__ import annotations

import hashlib
from dataclasses import dataclass

_DESKTOP_SIZES: tuple[tuple[int, int], ...] = (
    (1366, 768),
    (1440, 900),
    (1536, 864),
    (1600, 900),
    (1920, 1080),
    (1280, 800),
    (1280, 1024),
)


@dataclass(frozen=True, slots=True)
class ViewportSpec:
    width: int
    height: int
    mobile: bool
    device_scale_factor: float


def resolve_viewport(profile: str) -> ViewportSpec:
    """Map a fingerprint profile name to viewport / device metrics."""
    name = (profile or "").lower()

    if "safari_ios" in name or name.startswith("si"):
        return ViewportSpec(390, 844, True, 3.0)
    if "safari_ipad" in name or name.startswith("sp"):
        return ViewportSpec(820, 1180, True, 2.0)
    if "firefox_android" in name or "android" in name or name.startswith("fa"):
        return ViewportSpec(412, 915, True, 2.625)
    if "firefox" in name and "android" not in name:
        return ViewportSpec(1440, 900, False, 1.0)

    digest = hashlib.sha256(name.encode()).digest()
    idx = digest[0] % len(_DESKTOP_SIZES)
    width, height = _DESKTOP_SIZES[idx]
    return ViewportSpec(width, height, False, 1.0)
