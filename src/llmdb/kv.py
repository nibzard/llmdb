"""Thin typed KV API wrapping :mod:`lmdb`."""

from __future__ import annotations

import lmdb
from typing import Iterable, Tuple, Optional


class KV:
    """Minimal LMDB wrapper."""

    def __init__(self, path: str, readonly: bool = False) -> None:
        self.env = lmdb.open(path, readonly=readonly, max_dbs=1)

    def get(self, key: bytes) -> Optional[bytes]:
        with self.env.begin() as txn:
            return txn.get(key)

    def put(self, key: bytes, value: bytes) -> None:
        with self.env.begin(write=True) as txn:
            txn.put(key, value)

    def items(self) -> Iterable[Tuple[bytes, bytes]]:
        with self.env.begin() as txn:
            cursor = txn.cursor()
            for k, v in cursor:
                yield k, v

