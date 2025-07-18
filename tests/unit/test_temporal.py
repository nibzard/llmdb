from llmdb.temporal import MonotonicClock, now_ts
from llmdb.temporal_key import pack, unpack


def test_now_ts(monkeypatch):
    clock = MonotonicClock()
    t1 = now_ts(clock)
    t2 = now_ts(clock)
    assert t2 >= t1


def test_pack_roundtrip():
    key = (1, b"k", 2, 3)
    packed = pack(key)
    assert unpack(packed) == key
