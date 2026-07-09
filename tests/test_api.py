from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_health_old_path_returns_404():
    resp = client.get("/health")
    assert resp.status_code == 404
