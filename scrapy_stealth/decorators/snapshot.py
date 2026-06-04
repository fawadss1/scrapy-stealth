from __future__ import annotations

import functools
import os
from typing import Any, Callable

from ..utils.console import console


def snapshot(fn: Callable | None = None, *, path: str | Callable | None = None) -> Any:
    """
    Decorator that auto-saves a browser snapshot before the callback runs.

    Usage::

        @snapshot
        def parse(self, response): ...

        @snapshot()
        def parse(self, response): ...

        @snapshot(path="stealth_shots/page.png")
        def parse(self, response): ...

        @snapshot(path=lambda r: r.url.split("/")[-1] + ".png")
        def parse(self, response): ...

    Logs an error if ``meta={'stealth': {'snapshot': True}}`` was not set.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self: Any, response: Any, *args: Any, **kwargs: Any) -> Any:
            _save(response, path)
            return func(self, response, *args, **kwargs)

        return wrapper

    if fn is not None:
        if hasattr(fn, "meta"):
            raise TypeError(
                "snapshot is a decorator, not a callable method. "
                "Use @snapshot on your callback, or access "
                "response.meta['snapshot_content'] directly."
            )
        return decorator(fn)
    return decorator


def _save(response: Any, path: str | Callable | None) -> None:
    if callable(path):
        path = str(path(response))

    shot: bytes | None = response.meta.get("snapshot_content")
    if not shot:
        console.error(
            f"snapshot decorator called on {response.url!r} but no snapshot data found. "
            "Set meta={'stealth': {'driver'='browser', 'snapshot': True}} on the request."
        )
        return

    if path is None:
        import re
        from datetime import datetime

        safe = re.sub(r"\W", "_", response.url)[:20].strip("_")
        path = (
            f"stealth_snapshots/{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.png"
        )

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(shot)
    console.success(f"Snapshot saved → {os.path.abspath(path)}")
