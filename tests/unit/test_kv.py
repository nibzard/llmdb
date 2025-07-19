from llmdb.kv import KV
from llmdb.kv._codec import RawValue


def test_put_get(tmp_path):
    db = KV(str(tmp_path))
    key = (0, b"foo", 0, 0)
    db.put(key, RawValue(payload=b"bar"))
    val = db.get(key)
    assert isinstance(val, RawValue)
    assert val.payload == b"bar"


def test_delete(tmp_path):
    db = KV(str(tmp_path))
    key = (0, b"foo", 0, 0)
    db.put(key, RawValue(payload=b"bar"))
    assert db.delete(key) is True
    assert db.get(key) is None
    assert db.delete(key) is False
