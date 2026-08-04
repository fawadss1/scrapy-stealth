from __future__ import annotations

import contextlib
import threading
import time
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
        self._lock = threading.Lock()
        self._stores: list[dict[K, V]] = []

    def get(self, key: K) -> V:
        if not hasattr(self._local, "store"):
            store: dict[K, V] = {}
            with self._lock:
                self._stores.append(store)
            self._local.store = store
        store = self._local.store
        if key not in store:
            store[key] = self._factory(key)
        return store[key]

    def clear_all(self) -> None:
        """Drop every thread's cached sessions/clients (fresh TLS/cookies)."""
        with self._lock:
            for store in self._stores:
                for value in list(store.values()):
                    close = getattr(value, "close", None)
                    if callable(close):
                        with contextlib.suppress(Exception):
                            close()
                store.clear()


class BanStreakTracker:
    """Consecutive ban counter for session / browser recycling."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._streak = 0
        self._restart_due = False
        self._claimed = False
        self._last_restart = 0.0

    def record(self, banned: bool) -> bool:
        """Return True once per ban wave when a restart should be attempted.

        Concurrent threads may all see the streak threshold; only the first
        caller gets ``True`` until ``acknowledge_restart()`` completes.
        """
        from ..config import config

        with self._lock:
            if not banned:
                self._streak = 0
                self._restart_due = False
                return False

            self._streak += 1
            if self._streak >= config.get("STEALTH_RECYCLE_AFTER_BANS"):
                self._restart_due = True

            if not self._restart_due or self._claimed:
                return False
            cooldown = config.get("STEALTH_RECYCLE_COOLDOWN_S")
            if self._last_restart and time.monotonic() - self._last_restart < cooldown:
                return False

            self._claimed = True
            return True

    def acknowledge_restart(self) -> None:
        """Call when a ban-triggered session/browser restart is initiated."""
        with self._lock:
            self._streak = 0
            self._restart_due = False
            self._claimed = False
            self._last_restart = time.monotonic()

    @property
    def streak(self) -> int:
        with self._lock:
            return self._streak
