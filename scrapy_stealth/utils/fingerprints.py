from __future__ import annotations

_R: dict[str, list[tuple[str, int]]] = {
    "c":  [("130", 3), ("131", 3), ("132", 4), ("133", 4), ("134", 5), ("135", 6), ("136", 8), ("137", 10)],
    "e":  [("122", 2), ("127", 2), ("131", 3), ("134", 5)],
    "f":  [("133", 2), ("135", 2), ("136", 3), ("139", 4)],
    "fp": [("135", 1), ("136", 1)],
    "fa": [("135", 2)],
    "s":  [("18", 3), ("18_2", 3), ("18_3", 4), ("18_3_1", 4), ("18_5", 5)],
    "si": [("17_2", 2), ("17_4_1", 2), ("18_1_1", 6)],
    "sp": [("18", 2)],
    "o":  [("116", 1), ("117", 1), ("118", 2), ("119", 3)],
    "ok": [("4_10", 1), ("4_12", 1), ("5", 1)],
}

_P: dict[str, str] = {
    "c": "chrome", "e": "edge", "f": "firefox", "fp": "firefox_private",
    "fa": "firefox_android", "s": "safari", "si": "safari_ios",
    "sp": "safari_ipad", "o": "opera", "ok": "okhttp",
}


def _build() -> tuple[list[str], list[int]]:
    names: list[str] = []
    weights: list[int] = []
    for k, entries in _R.items():
        for v, w in entries:
            names.append(f"{_P[k]}_{v}")
            weights.append(w)
    return names, weights


POOL, WEIGHTS = _build()
