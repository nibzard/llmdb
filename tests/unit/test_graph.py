from llmdb.graph import Graph, Edge
from llmdb.kv import KV
from llmdb.temporal import MonotonicClock


def test_edges_roundtrip(tmp_path):
    kv = KV(str(tmp_path), clock=MonotonicClock())
    g = Graph(kv)
    edge1: Edge = (b"a", b"b", {"w": 1})
    edge2: Edge = (b"b", b"a", {"w": 2})
    g.put_edge(edge1, valid_from=1, tx_id=1)
    g.put_edge(edge2, valid_from=2, tx_id=2)

    out = list(g.out_edges(b"a", as_of_valid=2))
    assert len(out) == 1
    assert out[0][2]["w"] == 1
