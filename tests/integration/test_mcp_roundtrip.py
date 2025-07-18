

from mcp_server.server import create_app
from fastapi.testclient import TestClient


def test_ping_route():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"pong": "ok"}

