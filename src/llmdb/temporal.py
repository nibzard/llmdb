"""Bitemporal helpers."""

from __future__ import annotations


def now_ts() -> int:
    """Return current timestamp as integer.

    This placeholder uses monotonic time to remain deterministic in tests.
    """

    import time

    return int(time.monotonic() * 1_000_000)

