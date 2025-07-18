from __future__ import annotations

import struct

__all__ = ["Key", "pack", "unpack"]

Key = tuple[int, bytes, int, int]


def pack(key: Key) -> bytes:
    partition, user_key, valid_from, tx_id = key
    header = struct.pack(">IIQQ", partition, len(user_key), valid_from, tx_id)
    return header + user_key


def unpack(b: bytes) -> Key:
    partition, key_len, valid_from, tx_id = struct.unpack(">IIQQ", b[:24])
    user_key = b[24 : 24 + key_len]
    return partition, user_key, valid_from, tx_id
