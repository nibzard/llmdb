"""Graph façade stubs."""

from __future__ import annotations

__all__ = ["Graph", "NodeId", "Edge"]

import json
from typing import Any, Iterator

from .kv import KV
from .kv._codec import JSONValue
from .temporal_key import Key


NodeId = bytes
Edge = tuple[NodeId, NodeId, dict[str, Any]]


class Graph:
    """Simple graph façade backed by :class:`KV`."""

    def __init__(self, kv: KV) -> None:
        self.kv = kv

    def _edge_key(self, src: NodeId, dst: NodeId, valid_from: int, tx_id: int) -> Key:
        user_key = src + b"\x00" + dst
        return (1, user_key, valid_from, tx_id)

    def put_edge(self, e: Edge, *, valid_from: int, tx_id: int) -> None:
        src, dst, props = e
        payload = json.dumps(props).encode()
        self.kv.put(
            self._edge_key(src, dst, valid_from, tx_id), JSONValue(payload=payload)
        )

    def out_edges(self, node: NodeId, as_of_valid: int) -> Iterator[Edge]:
        for key, value in self.kv.items():
            partition, user_key, valid_from, _ = key
            if partition != 1 or valid_from > as_of_valid:
                continue
            src, dst = user_key.split(b"\x00", 1)
            if src != node:
                continue
            props = json.loads(value.payload.decode())
            yield (src, dst, props)
