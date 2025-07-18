"""Bitemporal helpers."""

from __future__ import annotations

__all__ = ["Clock", "MonotonicClock", "WallClock", "now_ts"]

import time
from typing import Protocol


class Clock(Protocol):
    def now_ts(self) -> int:
        """Return timestamp in microseconds."""


class MonotonicClock:
    def now_ts(self) -> int:
        return int(time.monotonic() * 1_000_000)


class WallClock:
    def now_ts(self) -> int:
        return int(time.time() * 1_000_000)


def now_ts(clock: Clock | None = None) -> int:
    """Return current timestamp using provided ``clock`` or :class:`MonotonicClock`."""

    clock = clock or MonotonicClock()
    return clock.now_ts()
