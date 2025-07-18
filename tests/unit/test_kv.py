from llmdb.kv import KV


def test_put_get(tmp_path):
    db = KV(str(tmp_path))
    db.put(b"foo", b"bar")
    assert db.get(b"foo") == b"bar"

