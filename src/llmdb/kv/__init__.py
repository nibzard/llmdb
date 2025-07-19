"""Thin typed KV API wrapping :mod:`lmdb`."""

from __future__ import annotations

__all__ = ["KV"]

import lmdb
from typing import Iterable, Optional

from ._codec import JSONValue, RawValue, Value, decode, encode
from ..temporal_key import Key, pack, unpack
from ..temporal import Clock, MonotonicClock


class KV:
    """Minimal LMDB wrapper using bitemporal keys and typed values."""

    def __init__(
        self, path: str, readonly: bool = False, *, clock: Clock = MonotonicClock()
    ) -> None:
        self.env = lmdb.open(path, readonly=readonly, max_dbs=1)
        self.clock = clock

    def get(self, key: Key) -> Optional[Value]:
        with self.env.begin() as txn:
            raw = txn.get(pack(key))
            return decode(raw) if raw is not None else None

    def put(self, key: Key, value: Value | bytes) -> None:
        if not isinstance(value, (RawValue, JSONValue)):
            value = RawValue(payload=value)
        with self.env.begin(write=True) as txn:
            txn.put(pack(key), encode(value))

    def items(self) -> Iterable[tuple[Key, Value]]:
        with self.env.begin() as txn:
            cursor = txn.cursor()
            for k, v in cursor:
                yield unpack(k), decode(v)

    def delete(self, key: Key) -> bool:
        """Remove ``key`` from the database."""
        encoded = pack(key)
        with self.env.begin(write=True) as txn:
            return bool(txn.delete(encoded))
