from __future__ import annotations

import threading
from typing import Callable, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class SessionCache(Generic[K, V]):
    """Lazy per-thread cache backed by a factory callable.

    Each thread gets its own isolated dict keyed by ``K``.  On the first
    access for a given key the factory is called once; subsequent accesses on
    the same thread return the cached instance.  No locking is needed because
    every thread operates on its own storage.

    Typical use: persistent HTTP sessions or clients that must not be shared
    across threads but should be reused within a thread.
    """

    def __init__(self, factory: Callable[[K], V]) -> None:
        self._factory = factory
        self._local = threading.local()

    def get(self, key: K) -> V:
        if not hasattr(self._local, "store"):
            self._local.store = {}
        if key not in self._local.store:
            self._local.store[key] = self._factory(key)
        return self._local.store[key]
