from __future__ import annotations

import importlib.util
import pathlib
import re


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
        if re.search(b"(?<!\xc2)\xb1", data):
            network_py.write_bytes(re.sub(b"(?<!\xc2)\xb1", b"\xc2\xb1", data))
    except Exception:
        pass
