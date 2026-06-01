from __future__ import annotations

import importlib.util
import pathlib


def patch_nodriver() -> None:
    """Fix Latin-1 byte in nodriver/cdp/network.py that causes SyntaxError on import."""
    try:
        spec = importlib.util.find_spec("nodriver")
        if spec is None or spec.origin is None:
            return
        network_py = pathlib.Path(spec.origin).parent / "cdp" / "network.py"
        if not network_py.exists():
            return
        data = network_py.read_bytes()
        if b"\xb1" in data:
            network_py.write_bytes(data.replace(b"\xb1", "\u00b1".encode()))
    except Exception:
        pass
