import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.database import get_db, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    tmp_db = tempfile.mktemp(suffix=".db")
    monkeypatch.setattr("src.config.settings.database_path", tmp_db)
    monkeypatch.setattr("src.config.settings.uploads_dir", tempfile.mkdtemp())
    init_db()
    yield
    try:
        os.remove(tmp_db)
    except OSError:
        pass


def test_register():
    resp = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate():
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    resp = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "other@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 409


def test_login():
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    resp = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "securepass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid():
    resp = client.post("/api/v1/auth/login", json={
        "username": "nobody",
        "password": "wrong",
    })
    assert resp.status_code == 401


def test_me():
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepass123",
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "securepass123",
    })
    token = login_resp.json()["access_token"]
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_me_unauthorized():
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_admin_only_as_analyst():
    client.post("/api/v1/auth/register", json={
        "username": "analyst1",
        "email": "a@a.com",
        "password": "pass",
    })
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "analyst1",
        "password": "pass",
    })
    token = login_resp.json()["access_token"]
    resp = client.get("/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_admin_only_as_admin():
    from src.services.auth import hash_password
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (username, email, hashed_password, role) VALUES (?, ?, ?, ?)",
            ("admin1", "admin@a.com", hash_password("pass"), "admin"),
        )
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "admin1",
        "password": "pass",
    })
    token = login_resp.json()["access_token"]
    resp = client.get("/api/v1/auth/admin-only", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "Welcome admin"
