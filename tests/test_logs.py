import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.database import get_db, init_db
from src.services.log_parser import (
    NGINX_ERROR_RE,
    detect_source_type,
    parse_line,
    parse_log,
    validate_file,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    tmp_db = tempfile.mktemp(suffix=".db")
    monkeypatch.setattr("src.config.settings.database_path", tmp_db)
    monkeypatch.setattr("src.config.settings.uploads_dir", tempfile.mkdtemp())
    init_db()
    client.post("/api/v1/auth/register", json={
        "username": "testuser", "email": "test@t.com", "password": "pass",
    })
    yield
    try:
        os.remove(tmp_db)
    except OSError:
        pass


def _token():
    resp = client.post("/api/v1/auth/login", json={"username": "testuser", "password": "pass"})
    return resp.json()["access_token"]


def _auth():
    return {"Authorization": f"Bearer {_token()}"}


# ── Upload tests ──

def test_upload_syslog():
    log = b"Sep 26 10:00:00 server sshd[1234]: Failed password for root from 10.0.0.1 port 22"
    resp = client.post("/api/v1/logs/upload", files={"file": ("auth.log", log, "text/plain")}, headers=_auth())
    assert resp.status_code == 201
    assert resp.json()["source_type"] == "syslog"
    assert resp.json()["event_count"] == 1


def test_upload_apache():
    log = b'192.168.1.1 - - [26/Sep/2026:12:00:00 +0000] "GET /admin HTTP/1.1" 404 1234'
    resp = client.post("/api/v1/logs/upload", files={"file": ("access.log", log, "text/plain")}, headers=_auth())
    assert resp.status_code == 201
    assert resp.json()["source_type"] == "apache"


def test_upload_generic():
    resp = client.post("/api/v1/logs/upload", files={"file": ("custom.log", b"something happened at 10.0.0.5", "text/plain")}, headers=_auth())
    assert resp.status_code == 201
    assert resp.json()["source_type"] == "generic"


def test_upload_nginx_access():
    log = b'10.0.0.1 - - [26/Sep/2026:12:00:00 +0000] "GET /api HTTP/1.1" 200 1234 "-" "curl/7.0"'
    resp = client.post("/api/v1/logs/upload", files={"file": ("nginx-access.log", log, "text/plain")}, headers=_auth())
    assert resp.status_code == 201
    assert resp.json()["source_type"] == "nginx"


def test_upload_nginx_error():
    log = b"2026/09/26 10:00:00 [error] 1234#0: *567 connect() failed (111: Connection refused)"
    resp = client.post("/api/v1/logs/upload", files={"file": ("nginx-error.log", log, "text/plain")}, headers=_auth())
    assert resp.status_code == 201
    assert resp.json()["source_type"] == "nginx"


def test_upload_windows_xml():
    log = b"""<?xml version="1.0"?>
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Test"/>
    <EventID>7036</EventID>
    <Level>2</Level>
    <TimeCreated SystemTime="2026-01-15T10:30:00.123Z"/>
    <Computer>SERVER01</Computer>
  </System>
</Event>"""
    resp = client.post("/api/v1/logs/upload", files={"file": ("application.evtx", log, "text/plain")}, headers=_auth())
    assert resp.status_code == 201
    assert resp.json()["source_type"] == "windows"


def test_upload_invalid_extension():
    resp = client.post("/api/v1/logs/upload", files={"file": ("malware.exe", b"bad", "application/octet-stream")}, headers=_auth())
    assert resp.status_code == 400
    assert "not allowed" in resp.json()["detail"].lower()


def test_upload_no_filename():
    resp = client.post("/api/v1/logs/upload", files={"file": ("", b"data", "text/plain")}, headers=_auth())
    assert resp.status_code == 422


def test_upload_unauthorized():
    resp = client.post("/api/v1/logs/upload", files={"file": ("test.log", b"data", "text/plain")})
    assert resp.status_code == 401


def test_list_logs():
    client.post("/api/v1/logs/upload", files={"file": ("test.log", b"line1\nline2", "text/plain")}, headers=_auth())
    resp = client.get("/api/v1/logs/", headers=_auth())
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_events():
    upload = client.post("/api/v1/logs/upload", files={"file": ("auth.log", b"Sep 26 10:00:00 server sshd[1234]: Failed password for root from 10.0.0.1 port 22", "text/plain")}, headers=_auth())
    log_id = upload.json()["id"]
    resp = client.get(f"/api/v1/logs/{log_id}/events", headers=_auth())
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_events_json():
    upload = client.post("/api/v1/logs/upload", files={"file": ("test.log", b"hello", "text/plain")}, headers=_auth())
    log_id = upload.json()["id"]
    resp = client.get(f"/api/v1/logs/{log_id}/events.json", headers=_auth())
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_events_not_found():
    resp = client.get("/api/v1/logs/999/events", headers=_auth())
    assert resp.status_code == 404


# ── Parser unit tests ──

def test_parse_syslog():
    result = parse_line("Sep 26 10:00:00 server sshd: error: connection refused", 0, "syslog")
    assert result["severity"] == "error"


def test_parse_syslog_iso():
    result = parse_line("2026-09-26T10:00:00.123Z server sshd[100]: Accepted publickey", 0, "syslog")
    assert result["severity"] == "info"
    assert result["source_ip"] == "server"


def test_parse_apache_404():
    result = parse_line('1.2.3.4 - - [26/Sep/2026:12:00:00 +0000] "GET /admin HTTP/1.1" 404 123', 0, "apache")
    assert result["severity"] == "error"
    assert result["source_ip"] == "1.2.3.4"
    assert "404" in result["event_type"]


def test_parse_apache_200():
    result = parse_line('1.2.3.4 - - [26/Sep/2026:12:00:00 +0000] "GET / HTTP/1.1" 200 456', 0, "apache")
    assert result["severity"] == "info"


def test_parse_nginx_error():
    result = parse_line('2026/09/26 10:00:00 [error] 1234#0: *567 connect() failed', 0, "nginx")
    assert result["severity"] == "error"
    assert result["event_type"] == "nginx_error"


def test_parse_nginx_access():
    result = parse_line('10.0.0.1 - - [26/Sep/2026:12:00:00 +0000] "POST /api HTTP/1.1" 500 789 "-" "python"', 0, "nginx")
    assert result["severity"] == "error"
    assert result["source_ip"] == "10.0.0.1"


def test_detect_by_filename():
    assert detect_source_type("", "auth.log") == "syslog"
    assert detect_source_type("", "nginx-access.log") == "nginx"
    assert detect_source_type("", "application.evtx") == "windows"
    assert detect_source_type("", "access.log") == "apache"
    assert detect_source_type("", "syslog") == "syslog"


def test_detect_by_content():
    assert detect_source_type('1.2.3.4 - - [26/Sep/2026:12:00:00 +0000] "GET / HTTP/1.1" 200 123', "custom.log") == "apache"
    assert detect_source_type("Sep 26 10:00:00 server sshd[100]: test", "custom.log") == "syslog"
    assert detect_source_type("<Event xmlns='http://microsoft.com/'>", "custom.log") == "windows"


def test_validate_file():
    validate_file("test.log", 1000)
    with pytest.raises(ValueError, match="not allowed"):
        validate_file("bad.exe", 100)
    with pytest.raises(ValueError, match="too large"):
        validate_file("big.log", 200 * 1024 * 1024)


def test_empty_lines_skipped():
    events = parse_log("line1\n\n\nline2")
    assert len(events) == 2


def test_windows_xml_parse():
    xml = """<?xml version="1.0"?>
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <Provider Name="Test"/>
    <EventID>7036</EventID>
    <Level>2</Level>
    <TimeCreated SystemTime="2026-01-15T10:30:00.123Z"/>
    <Computer>DC01</Computer>
  </System>
</Event>"""
    result = parse_log(xml, "windows")
    assert len(result) == 1
    assert result[0]["source_ip"] == "DC01"
    assert result[0]["event_type"] == "7036"
    assert result[0]["severity"] == "error"


def test_nginx_error_regex():
    assert NGINX_ERROR_RE.match('2026/09/26 10:00:00 [error] 1234#0: *567 connect() failed')
    assert NGINX_ERROR_RE.match('2026/09/26 10:00:00 [warn] 999#0: *1 upstream timed out')
    assert not NGINX_ERROR_RE.match('1.2.3.4 - - [26/Sep/2026:12:00:00 +0000] "GET / HTTP/1.1" 200 123')
