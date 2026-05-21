from __future__ import annotations

import importlib.util


def patch_nodriver() -> None:
    """Fix Latin-1 byte in nodriver/cdp/network.py that causes SyntaxError on import."""
    try:
        spec = importlib.util.find_spec("nodriver.cdp.network")
        if spec is None or spec.origin is None:
            return
        path = spec.origin
        with open(path, "rb") as f:
            data = f.read()
        if b"\xb1" in data:
            with open(path, "wb") as f:
                f.write(data.replace(b"\xb1", "\u00b1".encode()))
    except Exception:
        pass
