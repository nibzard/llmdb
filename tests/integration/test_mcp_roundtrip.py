from mcp_server.server import create_app
from fastapi.testclient import TestClient
from llmdb.kv import KV


def test_ping_route():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"pong": "ok"}


def test_put_get_delete(tmp_path):
    kv = KV(str(tmp_path))
    app = create_app(kv=kv)
    client = TestClient(app)

    r = client.put("/kv/aGVsbG8=", json={"value": "d29ybGQ="})
    assert r.status_code == 204
    assert client.get("/kv/aGVsbG8=").json() == {"value": "d29ybGQ="}
    assert client.delete("/kv/aGVsbG8").status_code == 204
