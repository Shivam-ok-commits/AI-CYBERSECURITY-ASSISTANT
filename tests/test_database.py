import os
import tempfile

import pytest

from src.database import get_db, get_connection, init_db


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    tmp = tempfile.mktemp(suffix=".db")
    monkeypatch.setattr("src.config.settings.database_path", tmp)
    init_db()
    yield
    try:
        os.remove(tmp)
    except OSError:
        pass


def test_init_db_creates_tables():
    conn = get_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [row["name"] for row in tables]
    assert "users" in table_names
    assert "uploaded_logs" in table_names
    assert "investigations" in table_names
    assert "reports" in table_names
    assert "chats" in table_names
    assert "threat_cache" in table_names
    conn.close()


def test_users_table_schema():
    conn = get_connection()
    cols = conn.execute("PRAGMA table_info(users)").fetchall()
    col_names = [c["name"] for c in cols]
    assert "username" in col_names
    assert "email" in col_names
    assert "hashed_password" in col_names
    assert "role" in col_names
    conn.close()


def test_uploaded_logs_fk():
    conn = get_connection()
    cols = conn.execute("PRAGMA table_info(uploaded_logs)").fetchall()
    col_names = [c["name"] for c in cols]
    assert "user_id" in col_names
    assert "filename" in col_names
    assert "filepath" in col_names
    assert "size_bytes" in col_names
    assert "source_type" in col_names
    assert "status" in col_names
    conn.close()


def test_investigations_table():
    conn = get_connection()
    cols = conn.execute("PRAGMA table_info(investigations)").fetchall()
    col_names = [c["name"] for c in cols]
    assert "title" in col_names
    assert "description" in col_names
    assert "status" in col_names
    assert "severity" in col_names
    assert "findings" in col_names
    conn.close()


def test_reports_table():
    conn = get_connection()
    cols = conn.execute("PRAGMA table_info(reports)").fetchall()
    col_names = [c["name"] for c in cols]
    assert "investigation_id" in col_names
    assert "title" in col_names
    assert "content" in col_names
    assert "format" in col_names
    conn.close()


def test_chats_table():
    conn = get_connection()
    cols = conn.execute("PRAGMA table_info(chats)").fetchall()
    col_names = [c["name"] for c in cols]
    assert "session_id" in col_names
    assert "role" in col_names
    assert "content" in col_names

    roles_check = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='chats'"
    ).fetchone()
    assert "CHECK" in roles_check["sql"].upper()
    conn.close()


def test_threat_cache_unique_indicator():
    with get_db() as conn:
        conn.execute(
            "INSERT INTO threat_cache (indicator, indicator_type, expires_at) VALUES (?, ?, ?)",
            ("8.8.8.8", "ip", "2026-12-31"),
        )
        with pytest.raises(Exception):
            conn.execute(
                "INSERT INTO threat_cache (indicator, indicator_type, expires_at) VALUES (?, ?, ?)",
                ("8.8.8.8", "ip", "2026-12-31"),
            )


def test_get_db_rollback_on_error():
    class FakeError(Exception):
        pass

    with pytest.raises(FakeError):
        with get_db() as conn:
            conn.execute(
                "INSERT INTO threat_cache (indicator, indicator_type, expires_at) VALUES (?, ?, ?)",
                ("rollback-test", "domain", "2026-12-31"),
            )
            raise FakeError()

    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM threat_cache WHERE indicator = ?", ("rollback-test",)
    ).fetchone()
    assert row is None
    conn.close()


def test_cascade_delete_user():
    with get_db() as conn:
        conn.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES (?, ?, ?)",
            ("delete-me", "del@x.com", "h"),
        )
        uid = conn.execute("SELECT id FROM users WHERE username = ?", ("delete-me",)).fetchone()["id"]
        conn.execute(
            "INSERT INTO uploaded_logs (user_id, filename, filepath) VALUES (?, ?, ?)",
            (uid, "test.log", "/tmp/test.log"),
        )
        conn.execute("DELETE FROM users WHERE id = ?", (uid,))
        logs = conn.execute(
            "SELECT id FROM uploaded_logs WHERE user_id = ?", (uid,)
        ).fetchall()
        assert len(logs) == 0
