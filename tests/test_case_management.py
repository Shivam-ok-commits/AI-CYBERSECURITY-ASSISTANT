import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.database import init_db

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


def _create_case(title="Test Case", **kw):
    payload = {"title": title, **kw}
    r = client.post("/api/v1/cases", json=payload, headers=_auth())
    assert r.status_code == 201
    return r.json()


# ── 6.3 Case Management ──

def test_create_case():
    data = _create_case()
    assert data["title"] == "Test Case"
    assert data["case_id"].startswith("CASE-")
    assert data["status"] == "open"
    assert data["severity"] == "medium"
    assert data["case_type"] == "incident"


def test_create_case_with_all_fields():
    data = _create_case(title="Phish Alert", case_type="phishing", severity="critical", assigned_analyst="jane", description="Phishing email detected")
    assert data["title"] == "Phish Alert"
    assert data["case_type"] == "phishing"
    assert data["severity"] == "critical"
    assert data["assigned_analyst"] == "jane"
    assert data["description"] == "Phishing email detected"


def test_create_case_invalid_type_defaults():
    data = _create_case(case_type="invalid")
    assert data["case_type"] == "incident"


def test_create_case_invalid_severity_defaults():
    data = _create_case(severity="unknown")
    assert data["severity"] == "medium"


def test_list_cases():
    _create_case(title="A")
    _create_case(title="B")
    r = client.get("/api/v1/cases", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_case():
    c = _create_case()
    r = client.get(f"/api/v1/cases/{c['id']}", headers=_auth())
    assert r.status_code == 200
    assert r.json()["case_id"] == c["case_id"]


def test_get_case_not_found():
    r = client.get("/api/v1/cases/9999", headers=_auth())
    assert r.status_code == 404


def test_update_case():
    c = _create_case()
    r = client.put(f"/api/v1/cases/{c['id']}", json={"title": "Updated", "status": "in_progress"}, headers=_auth())
    assert r.status_code == 200
    assert r.json()["title"] == "Updated"
    assert r.json()["status"] == "in_progress"


def test_update_case_not_found():
    r = client.put("/api/v1/cases/9999", json={"title": "Nope"}, headers=_auth())
    assert r.status_code == 404


def test_archive_case():
    c = _create_case()
    r = client.post(f"/api/v1/cases/{c['id']}/archive", headers=_auth())
    assert r.status_code == 200
    assert r.json()["is_archived"] is True


def test_restore_case():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/archive", headers=_auth())
    r = client.post(f"/api/v1/cases/{c['id']}/restore", headers=_auth())
    assert r.status_code == 200
    assert r.json()["is_archived"] is False


def test_close_case():
    c = _create_case()
    r = client.put(f"/api/v1/cases/{c['id']}", json={"status": "closed"}, headers=_auth())
    assert r.status_code == 200
    assert r.json()["status"] == "closed"
    assert r.json()["closed_at"] is not None


# ── 6.4 Evidence Management ──

def test_add_evidence():
    c = _create_case()
    r = client.post(f"/api/v1/cases/{c['id']}/evidence", json={"evidence_type": "file", "file_name": "malware.exe", "description": "Suspicious binary"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["evidence_type"] == "file"
    assert r.json()["file_name"] == "malware.exe"


def test_add_evidence_invalid_type():
    c = _create_case()
    r = client.post(f"/api/v1/cases/{c['id']}/evidence", json={"evidence_type": "unknown"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["evidence_type"] == "other"


def test_add_evidence_case_not_found():
    r = client.post("/api/v1/cases/9999/evidence", json={"evidence_type": "file"}, headers=_auth())
    assert r.status_code == 404


def test_list_evidence():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/evidence", json={"evidence_type": "screenshot", "file_name": "screen.png"}, headers=_auth())
    client.post(f"/api/v1/cases/{c['id']}/evidence", json={"evidence_type": "ioc", "description": "8.8.8.8"}, headers=_auth())
    r = client.get(f"/api/v1/cases/{c['id']}/evidence", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_remove_evidence():
    c = _create_case()
    e = client.post(f"/api/v1/cases/{c['id']}/evidence", json={"evidence_type": "file", "file_name": "bad.exe"}, headers=_auth()).json()
    r = client.delete(f"/api/v1/cases/{c['id']}/evidence/{e['id']}", headers=_auth())
    assert r.status_code == 204


def test_remove_evidence_not_found():
    c = _create_case()
    r = client.delete(f"/api/v1/cases/{c['id']}/evidence/9999", headers=_auth())
    assert r.status_code == 404


# ── 6.1 Incident Report Generator ──

def test_generate_report():
    c = _create_case()
    payload = {
        "title": "Breach Report",
        "executive_summary": "A breach occurred",
        "technical_summary": "CVE-2024-1234 exploited",
        "ioc_list": [{"type": "ip", "value": "10.0.0.5", "context": "C2"}],
        "mitre_mapping": [{"technique_id": "T1059", "technique_name": "Command and Scripting Interpreter", "tactic": "Execution"}],
    }
    r = client.post(f"/api/v1/cases/{c['id']}/reports", json=payload, headers=_auth())
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Breach Report"
    assert "breach occurred" in data["content"]
    assert data["format"] == "markdown"


def test_generate_report_case_not_found():
    r = client.post("/api/v1/cases/9999/reports", json={"title": "R"}, headers=_auth())
    assert r.status_code == 404


def test_list_reports():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/reports", json={"title": "R1"}, headers=_auth())
    client.post(f"/api/v1/cases/{c['id']}/reports", json={"title": "R2"}, headers=_auth())
    r = client.get(f"/api/v1/cases/{c['id']}/reports", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) == 2


# ── 6.2 Report Export ──

def test_export_report_markdown():
    c = _create_case()
    rp = client.post(f"/api/v1/cases/{c['id']}/reports", json={"title": "Export Test", "executive_summary": "Test"}, headers=_auth()).json()
    r = client.get(f"/api/v1/cases/{c['id']}/reports/{rp['id']}/export?fmt=markdown", headers=_auth())
    assert r.status_code == 200
    assert "text/markdown" in r.headers["content-type"]


def test_export_report_html():
    c = _create_case()
    rp = client.post(f"/api/v1/cases/{c['id']}/reports", json={"title": "HTML Test"}, headers=_auth()).json()
    r = client.get(f"/api/v1/cases/{c['id']}/reports/{rp['id']}/export?fmt=html", headers=_auth())
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_export_report_json():
    c = _create_case()
    rp = client.post(f"/api/v1/cases/{c['id']}/reports", json={"title": "JSON Test"}, headers=_auth()).json()
    r = client.get(f"/api/v1/cases/{c['id']}/reports/{rp['id']}/export?fmt=json", headers=_auth())
    assert r.status_code == 200
    assert "json" in r.headers["content-type"]


def test_export_report_not_found():
    c = _create_case()
    r = client.get(f"/api/v1/cases/{c['id']}/reports/9999/export?fmt=markdown", headers=_auth())
    assert r.status_code == 404


# ── 6.5 Investigation Timeline ──

def test_get_timeline():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/evidence", json={"evidence_type": "file", "file_name": "bad.exe"}, headers=_auth())
    client.post(f"/api/v1/cases/{c['id']}/notes", json={"content": "Initial analysis started"}, headers=_auth())
    r = client.get(f"/api/v1/cases/{c['id']}/timeline", headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert "events" in data
    assert "critical_events" in data
    assert "attack_stages" in data
    assert "summary" in data
    assert len(data["events"]) >= 2


def test_get_timeline_case_not_found():
    r = client.get("/api/v1/cases/9999/timeline", headers=_auth())
    assert r.status_code == 404


# ── 6.7 Collaboration ──

def test_add_comment():
    c = _create_case()
    r = client.post(f"/api/v1/cases/{c['id']}/comments", json={"content": "Need to check this IP"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["content"] == "Need to check this IP"
    assert r.json()["is_internal"] is False


def test_add_internal_note():
    c = _create_case()
    r = client.post(f"/api/v1/cases/{c['id']}/comments", json={"content": "Internal note", "is_internal": True}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["is_internal"] is True


def test_list_comments():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/comments", json={"content": "C1"}, headers=_auth())
    client.post(f"/api/v1/cases/{c['id']}/comments", json={"content": "C2"}, headers=_auth())
    r = client.get(f"/api/v1/cases/{c['id']}/comments", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_list_comments_excludes_internal():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/comments", json={"content": "Public"}, headers=_auth())
    client.post(f"/api/v1/cases/{c['id']}/comments", json={"content": "Private", "is_internal": True}, headers=_auth())
    r = client.get(f"/api/v1/cases/{c['id']}/comments", headers=_auth())
    assert len(r.json()) == 1
    assert r.json()[0]["content"] == "Public"


def test_list_comments_includes_internal_when_requested():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/comments", json={"content": "Public"}, headers=_auth())
    client.post(f"/api/v1/cases/{c['id']}/comments", json={"content": "Private", "is_internal": True}, headers=_auth())
    r = client.get(f"/api/v1/cases/{c['id']}/comments?internal=true", headers=_auth())
    assert len(r.json()) == 2


def test_add_comment_case_not_found():
    r = client.post("/api/v1/cases/9999/comments", json={"content": "Hi"}, headers=_auth())
    assert r.status_code == 404


def test_notes():
    c = _create_case()
    r = client.post(f"/api/v1/cases/{c['id']}/notes", json={"content": "My note"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["is_internal"] is True
    r = client.get(f"/api/v1/cases/{c['id']}/notes", headers=_auth())
    assert len(r.json()) == 1


# ── 6.6 Report Templates ──

def test_list_templates():
    r = client.get("/api/v1/cases/templates")
    assert r.status_code == 200
    assert len(r.json()) >= 5


def test_get_template():
    r = client.get("/api/v1/cases/templates/1")
    assert r.status_code == 200
    assert r.json()["name"] == "malware_incident"


def test_get_template_not_found():
    r = client.get("/api/v1/cases/templates/9999")
    assert r.status_code == 404


def test_create_template():
    r = client.post("/api/v1/cases/templates", json={"name": "ransomware", "category": "malware", "content": "## Ransomware Report\n\n{{executive_summary}}"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["name"] == "ransomware"


def test_render_template():
    client.post("/api/v1/cases/templates", json={"name": "test_tmpl", "content": "Executive: {{executive_summary}}\nIOCs:\n{{ioc_list}}"}, headers=_auth())
    t = client.get("/api/v1/cases/templates?name=test_tmpl")
    r = client.post(f"/api/v1/cases/templates/1/render", json={"executive_summary": "Breach found", "ioc_list": ["10.0.0.1", "evil.com"]})
    assert r.status_code == 200
    assert "Breach found" in r.json()["content"]


# ── 6.8 Search & Archive ──

def test_search_cases():
    _create_case(title="Phishing Alert")
    _create_case(title="Malware Outbreak")
    r = client.get("/api/v1/cases/search/find?query=Phishing", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert "Phishing" in r.json()[0]["title"]


def test_search_cases_by_status():
    c = _create_case()
    client.put(f"/api/v1/cases/{c['id']}", json={"status": "closed"}, headers=_auth())
    r = client.get("/api/v1/cases/search/find?status=closed", headers=_auth())
    assert len(r.json()) == 1


def test_search_cases_by_severity():
    _create_case(title="Critical One", severity="critical")
    _create_case(title="Low One", severity="low")
    r = client.get("/api/v1/cases/search/find?severity=critical", headers=_auth())
    assert len(r.json()) == 1


def test_search_cases_by_analyst():
    _create_case(title="Assigned", assigned_analyst="alice")
    r = client.get("/api/v1/cases/search/find?assigned_analyst=alice", headers=_auth())
    assert len(r.json()) == 1


def test_archived_cases():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/archive", headers=_auth())
    r = client.get("/api/v1/cases/archived/list", headers=_auth())
    assert len(r.json()) == 1


# ── 6.9 Activity & Audit ──

def test_case_activity():
    c = _create_case()
    client.post(f"/api/v1/cases/{c['id']}/evidence", json={"evidence_type": "file", "file_name": "bad.exe"}, headers=_auth())
    r = client.get(f"/api/v1/cases/{c['id']}/activity", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) >= 2
    assert r.json()[0]["action"]


def test_case_activity_not_found():
    r = client.get("/api/v1/cases/9999/activity", headers=_auth())
    assert r.status_code == 404


def test_audit_log():
    _create_case(title="Auditable")
    r = client.get("/api/v1/cases/audit/logs", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert r.json()[0]["action"]


def test_audit_log_filter_by_entity():
    _create_case(title="Case A")
    r = client.get("/api/v1/cases/audit/logs?entity_type=case", headers=_auth())
    assert len(r.json()) >= 1


# ── Full report generation with all sections ──

def test_full_report_all_sections():
    c = _create_case()
    payload = {
        "title": "Complete Incident Report",
        "executive_summary": "Executive: A sophisticated attack was detected",
        "technical_summary": "Technical: CVE-2024-1234 exploited via phishing",
        "attack_timeline": [
            {"timestamp": "2024-01-01 00:00", "event": "Phishing email sent"},
            {"timestamp": "2024-01-01 01:00", "event": "Malware downloaded"},
        ],
        "ioc_list": [
            {"type": "ip", "value": "10.0.0.1", "context": "C2 Server"},
            {"type": "hash", "value": "d41d8cd98f00b204e9800998ecf8427e", "context": "Malware hash"},
        ],
        "mitre_mapping": [
            {"technique_id": "T1566", "technique_name": "Phishing", "tactic": "Initial Access"},
            {"technique_id": "T1059", "technique_name": "Command and Scripting Interpreter", "tactic": "Execution"},
        ],
        "root_cause": "Unpatched email gateway allowed phishing",
        "impact_assessment": "3 systems compromised, data exfiltrated",
        "containment_steps": ["Block C2 IPs", "Isolate affected hosts", "Reset credentials"],
        "recovery_steps": ["Restore from backup", "Patch vulnerability", "Deploy EDR"],
        "lessons_learned": "Implement email filtering, improve user awareness training",
    }
    r = client.post(f"/api/v1/cases/{c['id']}/reports", json=payload, headers=_auth())
    assert r.status_code == 201
    data = r.json()
    assert "Executive" in data["content"]
    assert "Technical" in data["content"]
    assert "Phishing" in data["content"]
    assert "C2 Server" in data["content"]
    assert "T1566" in data["content"]
    assert "Unpatched" in data["content"]
    assert "3 systems" in data["content"]
    assert "Block C2" in data["content"]
    assert "Restore from backup" in data["content"]
    assert "Implement email" in data["content"]


# ── Cross-phase: link evidence to real IOCs ──

def test_evidence_with_iocs():
    c = _create_case()
    r = client.post(f"/api/v1/cases/{c['id']}/evidence", json={"evidence_type": "ioc", "description": "8.8.8.8 - Command & Control", "source": "threat_intel"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["evidence_type"] == "ioc"


# ── Edge cases ──

def test_unauthorized_access():
    r = client.get("/api/v1/cases")
    assert r.status_code == 401
    r = client.post("/api/v1/cases", json={"title": "X"})
    assert r.status_code == 401


def test_different_user_cannot_access():
    c = _create_case()
    client.post("/api/v1/auth/register", json={"username": "other", "email": "b@b.com", "password": "pass"})
    r = client.post("/api/v1/auth/login", json={"username": "other", "password": "pass"})
    other_auth = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.get(f"/api/v1/cases/{c['id']}", headers=other_auth)
    assert r.status_code == 404


def test_export_all_formats():
    c = _create_case()
    rp = client.post(f"/api/v1/cases/{c['id']}/reports", json={"title": "Multi-format"}, headers=_auth()).json()
    for fmt in ("markdown", "html", "json"):
        r = client.get(f"/api/v1/cases/{c['id']}/reports/{rp['id']}/export?fmt={fmt}", headers=_auth())
        assert r.status_code == 200


def test_template_render_with_lists():
    ct = client.post("/api/v1/cases/templates", json={"name": "list_tmpl", "content": "IOCs:\n{{ioc_list}}"}, headers=_auth()).json()
    r = client.post(f"/api/v1/cases/templates/{ct['id']}/render", json={"ioc_list": ["1.1.1.1", "2.2.2.2"]})
    assert r.status_code == 200
    assert "1.1.1.1" in r.json()["content"]
    assert "2.2.2.2" in r.json()["content"]


def test_report_with_attack_stages():
    c = _create_case()
    payload = {
        "title": "Attack Stage Report",
        "attack_timeline": [
            {"timestamp": "00:00", "event": "Login attempt"},
            {"timestamp": "00:05", "event": "Persistence via service"},
        ],
        "executive_summary": "Multi-stage attack detected",
    }
    r = client.post(f"/api/v1/cases/{c['id']}/reports", json=payload, headers=_auth())
    assert r.status_code == 201
    assert "Login attempt" in r.json()["content"]
    assert "Persistence" in r.json()["content"]
