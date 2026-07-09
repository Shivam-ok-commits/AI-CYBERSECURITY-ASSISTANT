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


def _upload_log():
    log = b"Sep 26 10:00:00 server sshd[1234]: Failed password for root from 10.0.0.1 port 22\n"
    r = client.post("/api/v1/logs/upload", files={"file": ("auth.log", log, "text/plain")}, headers=_auth())
    return r.json()["id"]


# ── 8.1 Detection Rules ──

def test_create_detection_rule():
    r = client.post("/api/v1/detection/rules", json={"name": "Brute Force Detect", "category": "brute_force", "severity": "high", "content": "failed password"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["name"] == "Brute Force Detect"
    assert r.json()["enabled"] is True


def test_create_detection_rule_minimal():
    r = client.post("/api/v1/detection/rules", json={"name": "Simple Rule"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["rule_type"] == "custom"


def test_list_rules():
    client.post("/api/v1/detection/rules", json={"name": "R1", "category": "malware"}, headers=_auth())
    client.post("/api/v1/detection/rules", json={"name": "R2", "category": "phishing"}, headers=_auth())
    r = client.get("/api/v1/detection/rules")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_filter_rules_by_category():
    client.post("/api/v1/detection/rules", json={"name": "Malware Rule", "category": "malware"}, headers=_auth())
    r = client.get("/api/v1/detection/rules?category=malware")
    assert len(r.json()) == 1


def test_filter_rules_enabled():
    r1 = client.post("/api/v1/detection/rules", json={"name": "Enabled"}, headers=_auth()).json()
    client.put(f"/api/v1/detection/rules/{r1['id']}", json={"enabled": False}, headers=_auth())
    r = client.get("/api/v1/detection/rules?enabled_only=true")
    assert len(r.json()) == 0


def test_get_rule():
    r1 = client.post("/api/v1/detection/rules", json={"name": "Get Me"}, headers=_auth()).json()
    r = client.get(f"/api/v1/detection/rules/{r1['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Get Me"


def test_get_rule_not_found():
    r = client.get("/api/v1/detection/rules/9999")
    assert r.status_code == 404


def test_update_rule():
    r1 = client.post("/api/v1/detection/rules", json={"name": "Old"}, headers=_auth()).json()
    r = client.put(f"/api/v1/detection/rules/{r1['id']}", json={"name": "New", "severity": "critical"}, headers=_auth())
    assert r.status_code == 200
    assert r.json()["name"] == "New"
    assert r.json()["severity"] == "critical"


def test_toggle_rule():
    r1 = client.post("/api/v1/detection/rules", json={"name": "Toggle"}, headers=_auth()).json()
    r = client.put(f"/api/v1/detection/rules/{r1['id']}", json={"enabled": False}, headers=_auth())
    assert r.json()["enabled"] is False
    r = client.put(f"/api/v1/detection/rules/{r1['id']}", json={"enabled": True}, headers=_auth())
    assert r.json()["enabled"] is True


def test_delete_rule():
    r1 = client.post("/api/v1/detection/rules", json={"name": "Delete"}, headers=_auth()).json()
    r = client.delete(f"/api/v1/detection/rules/{r1['id']}")
    assert r.status_code == 204
    r = client.get(f"/api/v1/detection/rules/{r1['id']}")
    assert r.status_code == 404


def test_test_rule_regex():
    r1 = client.post("/api/v1/detection/rules", json={"name": "Regex Test", "rule_format": "regex", "content": "failed.*password"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/rules/{r1['id']}/test", json=["Failed password for root", "normal line"])
    assert r.status_code == 200
    assert r.json()["matched"] is True
    assert len(r.json()["matches"]) == 1


def test_test_rule_keyword():
    r1 = client.post("/api/v1/detection/rules", json={"name": "Keyword Test", "content": "malware suspicious"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/rules/{r1['id']}/test", json=["This is malware detected", "clean line"])
    assert r.status_code == 200
    assert r.json()["matched"] is True


def test_test_rule_no_match():
    r1 = client.post("/api/v1/detection/rules", json={"name": "No Match", "content": "xxx_yyy_zzz"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/rules/{r1['id']}/test", json=["clean log entry"])
    assert r.json()["matched"] is False


# ── 8.2 Sigma Rules ──

def test_create_sigma_rule():
    r = client.post("/api/v1/detection/sigma", json={"title": "Suspicious PowerShell", "level": "high", "detection": '{"keywords": ["powershell", "-enc"]}'})
    assert r.status_code == 201
    assert r.json()["title"] == "Suspicious PowerShell"
    assert r.json()["rule_id"].startswith("SIGMA-")


def test_list_sigma_rules():
    client.post("/api/v1/detection/sigma", json={"title": "S1", "level": "high"})
    client.post("/api/v1/detection/sigma", json={"title": "S2", "level": "low"})
    r = client.get("/api/v1/detection/sigma")
    assert len(r.json()) == 2


def test_get_sigma_rule():
    s = client.post("/api/v1/detection/sigma", json={"title": "Get Sigma"}).json()
    r = client.get(f"/api/v1/detection/sigma/{s['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Get Sigma"


def test_delete_sigma_rule():
    s = client.post("/api/v1/detection/sigma", json={"title": "Delete Sigma"}).json()
    r = client.delete(f"/api/v1/detection/sigma/{s['id']}")
    assert r.status_code == 204


def test_validate_sigma_valid():
    r = client.post("/api/v1/detection/sigma/validate?content=%7B%22title%22%3A%22Test%22%2C%22detection%22%3A%7B%22condition%22%3A%22keywords%22%7D%7D")
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_validate_sigma_invalid():
    r = client.post("/api/v1/detection/sigma/validate?content=not-json")
    assert r.status_code == 200
    assert r.json()["valid"] is False


def test_execute_sigma_rule():
    s = client.post("/api/v1/detection/sigma", json={"title": "Exec Sigma", "detection": '{"keywords": ["failed", "password"]}'}).json()
    r = client.post(f"/api/v1/detection/sigma/{s['id']}/execute", json=[{"id": 1, "raw": "Failed password for root"}, {"id": 2, "raw": "normal line"}])
    assert r.status_code == 200
    assert r.json()["matched"] is True


def test_export_sigma_rule():
    s = client.post("/api/v1/detection/sigma", json={"title": "Export Sigma", "author": "test", "level": "high", "detection": '{"condition": "keywords"}'}).json()
    r = client.get(f"/api/v1/detection/sigma/{s['id']}/export")
    assert r.status_code == 200
    assert r.json()["title"] == "Export Sigma"
    assert r.json()["author"] == "test"


# ── 8.3 YARA Rules ──

def test_create_yara_rule():
    r = client.post("/api/v1/detection/yara", json={"name": "DetectMalware", "content": "rule DetectMalware { strings: $s1 = \"malware\" condition: $s1 }"})
    assert r.status_code == 201
    assert r.json()["name"] == "DetectMalware"


def test_list_yara_rules():
    client.post("/api/v1/detection/yara", json={"name": "Y1", "content": "rule Y1 { condition: true }"})
    client.post("/api/v1/detection/yara", json={"name": "Y2", "content": "rule Y2 { condition: true }"})
    r = client.get("/api/v1/detection/yara")
    assert len(r.json()) == 2


def test_get_yara_rule():
    y = client.post("/api/v1/detection/yara", json={"name": "GetYara", "content": "rule GetYara { condition: true }"}).json()
    r = client.get(f"/api/v1/detection/yara/{y['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "GetYara"


def test_delete_yara_rule():
    y = client.post("/api/v1/detection/yara", json={"name": "DelYara", "content": "rule DelYara { condition: true }"}).json()
    r = client.delete(f"/api/v1/detection/yara/{y['id']}")
    assert r.status_code == 204


def test_validate_yara_valid():
    r = client.post("/api/v1/detection/yara/validate?content=rule+Test+%7B+condition%3A+true+%7D")
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_validate_yara_invalid():
    r = client.post("/api/v1/detection/yara/validate?content=invalid")
    assert r.status_code == 200
    assert r.json()["valid"] is False


def test_scan_yara():
    y = client.post("/api/v1/detection/yara", json={"name": "ScanMalware", "content": "rule ScanMalware { strings: $s1 = \"malware\" condition: $s1 }"}).json()
    r = client.post(f"/api/v1/detection/yara/{y['id']}/scan", json=["clean file content", "this file has malware inside"])
    assert r.status_code == 200
    assert r.json()["matched"] is True
    assert len(r.json()["matches"]) == 1


def test_scan_yara_no_match():
    y = client.post("/api/v1/detection/yara", json={"name": "NoMatch", "content": "rule NoMatch { strings: $s1 = \"evil\" condition: $s1 }"}).json()
    r = client.post(f"/api/v1/detection/yara/{y['id']}/scan", json=["clean content"])
    assert r.json()["matched"] is False


# ── 8.4 Threat Hunting ──

def test_create_hunt():
    r = client.post("/api/v1/detection/hunts", json={"name": "Hunt for IOCs", "hunt_type": "ioc"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["hunt_type"] == "ioc"


def test_list_hunts():
    client.post("/api/v1/detection/hunts", json={"name": "H1", "hunt_type": "log"}, headers=_auth())
    client.post("/api/v1/detection/hunts", json={"name": "H2", "hunt_type": "network"}, headers=_auth())
    r = client.get("/api/v1/detection/hunts", headers=_auth())
    assert len(r.json()) == 2


def test_get_hunt():
    h = client.post("/api/v1/detection/hunts", json={"name": "My Hunt"}, headers=_auth()).json()
    r = client.get(f"/api/v1/detection/hunts/{h['id']}", headers=_auth())
    assert r.status_code == 200


def test_delete_hunt():
    h = client.post("/api/v1/detection/hunts", json={"name": "Delete Hunt"}, headers=_auth()).json()
    r = client.delete(f"/api/v1/detection/hunts/{h['id']}", headers=_auth())
    assert r.status_code == 204


def test_execute_hunt_log():
    _upload_log()
    h = client.post("/api/v1/detection/hunts", json={"name": "Log Hunt", "hunt_type": "log", "query": "failed"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/hunts/{h['id']}/execute", headers=_auth())
    assert r.status_code == 200
    assert r.json()["total_results"] >= 1


def test_execute_hunt_ioc():
    from src.database import get_db
    from src.services.ioc_extractor import extract_iocs
    _upload_log()
    h = client.post("/api/v1/detection/hunts", json={"name": "IOC Hunt", "hunt_type": "ioc", "query": "10.0.0.1"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/hunts/{h['id']}/execute", headers=_auth())
    assert r.status_code == 200


def test_execute_hunt_not_found():
    r = client.post("/api/v1/detection/hunts/9999/execute", headers=_auth())
    assert r.status_code == 404


def test_hunt_results():
    _upload_log()
    h = client.post("/api/v1/detection/hunts", json={"name": "Results Hunt", "hunt_type": "log", "query": "failed"}, headers=_auth()).json()
    client.post(f"/api/v1/detection/hunts/{h['id']}/execute", headers=_auth())
    r = client.get("/api/v1/detection/hunts/results", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ── 8.5 Scheduled Scans ──

def test_create_job():
    r = client.post("/api/v1/detection/jobs", json={"name": "Daily Scan", "job_type": "log_analysis", "schedule_interval": "daily"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["job_type"] == "log_analysis"


def test_list_jobs():
    client.post("/api/v1/detection/jobs", json={"name": "J1", "job_type": "log_analysis"}, headers=_auth())
    client.post("/api/v1/detection/jobs", json={"name": "J2", "job_type": "ioc_check"}, headers=_auth())
    r = client.get("/api/v1/detection/jobs", headers=_auth())
    assert len(r.json()) == 2


def test_update_job():
    j = client.post("/api/v1/detection/jobs", json={"name": "Old Job", "job_type": "log_analysis"}, headers=_auth()).json()
    r = client.put(f"/api/v1/detection/jobs/{j['id']}", json={"is_active": False}, headers=_auth())
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_delete_job():
    j = client.post("/api/v1/detection/jobs", json={"name": "Del Job", "job_type": "log_analysis"}, headers=_auth()).json()
    r = client.delete(f"/api/v1/detection/jobs/{j['id']}")
    assert r.status_code == 204


def test_run_job():
    j = client.post("/api/v1/detection/jobs", json={"name": "Run Job", "job_type": "log_analysis"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/jobs/{j['id']}/run")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"


# ── 8.6 Alert Automation ──

def test_create_automation():
    r = client.post("/api/v1/detection/automation", json={"name": "Escalate Critical", "trigger_type": "alert_severity", "conditions": '{"severity": "critical"}', "actions": '["create_case", "notify_admin"]', "priority": 10})
    assert r.status_code == 201
    assert r.json()["trigger_type"] == "alert_severity"


def test_list_automation():
    client.post("/api/v1/detection/automation", json={"name": "A1", "trigger_type": "alert_created"})
    client.post("/api/v1/detection/automation", json={"name": "A2", "trigger_type": "alert_severity"})
    r = client.get("/api/v1/detection/automation")
    assert len(r.json()) == 2


def test_update_automation():
    a = client.post("/api/v1/detection/automation", json={"name": "Old Auto", "trigger_type": "alert_created"}).json()
    r = client.put(f"/api/v1/detection/automation/{a['id']}", json={"is_active": False})
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_delete_automation():
    a = client.post("/api/v1/detection/automation", json={"name": "Del Auto", "trigger_type": "alert_created"}).json()
    r = client.delete(f"/api/v1/detection/automation/{a['id']}")
    assert r.status_code == 204


# ── 8.7 AI Rule Generator ──

def test_ai_generate_sigma():
    r = client.post("/api/v1/detection/ai/generate-sigma?text=Detect+malware+execution")
    assert r.status_code == 200
    assert "malware" in r.json()["content"].lower()


def test_ai_generate_sigma_brute():
    r = client.post("/api/v1/detection/ai/generate-sigma?text=Detect+brute+force+password+attack")
    assert r.status_code == 200
    assert "failed password" in r.json()["content"].lower()


def test_ai_generate_yara():
    r = client.post("/api/v1/detection/ai/generate-yara?text=Ransomware+that+encrypts+files")
    assert r.status_code == 200
    assert "rule " in r.json()["content"]


def test_ai_generate_yara_phishing():
    r = client.post("/api/v1/detection/ai/generate-yara?text=Phishing+email+detection")
    assert r.status_code == 200
    assert "rule " in r.json()["content"]


def test_ai_explain_yara():
    r = client.post("/api/v1/detection/ai/explain?content=rule+Test+%7B+strings%3A+%24s1+%3D+%22malware%22+condition%3A+%24s1+%7D")
    assert r.status_code == 200
    assert "YARA" in r.json()["explanation"]


def test_ai_explain_sigma():
    r = client.post("/api/v1/detection/ai/explain?content=%7B%22title%22%3A%22Test%22%2C%22level%22%3A%22high%22%7D")
    assert r.status_code == 200
    assert "Sigma" in r.json()["explanation"]


def test_ai_improve_rule():
    r = client.post("/api/v1/detection/ai/improve?content=rule+Test+%7B+strings%3A+%24s1+%3D+%22bad%22+condition%3A+%24s1+%7D&suggestion=Add+more+strings")
    assert r.status_code == 200
    assert "Improvement" in r.json()["content"]


# ── 8.8 Workflow Playbooks ──

def test_create_playbook():
    r = client.post("/api/v1/detection/playbooks", json={"name": "Phishing Response", "category": "phishing", "steps": "[\"Isolate host\", \"Collect email\"]"})
    assert r.status_code == 201
    assert r.json()["name"] == "Phishing Response"


def test_list_playbooks():
    client.post("/api/v1/detection/playbooks", json={"name": "P1", "category": "malware"})
    client.post("/api/v1/detection/playbooks", json={"name": "P2", "category": "phishing"})
    r = client.get("/api/v1/detection/playbooks")
    assert len(r.json()) == 2


def test_get_playbook():
    p = client.post("/api/v1/detection/playbooks", json={"name": "Get PB"}).json()
    r = client.get(f"/api/v1/detection/playbooks/{p['id']}")
    assert r.status_code == 200


def test_delete_playbook():
    p = client.post("/api/v1/detection/playbooks", json={"name": "Del PB"}).json()
    r = client.delete(f"/api/v1/detection/playbooks/{p['id']}")
    assert r.status_code == 204


# ── 8.9 Hunting Reports ──

def test_create_hunting_report():
    r = client.post("/api/v1/detection/reports", json={"title": "Q1 Hunt", "hunt_type": "log", "summary": "Found suspicious activity"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["title"] == "Q1 Hunt"


def test_list_hunting_reports():
    client.post("/api/v1/detection/reports", json={"title": "R1", "hunt_type": "log"}, headers=_auth())
    client.post("/api/v1/detection/reports", json={"title": "R2", "hunt_type": "ioc"}, headers=_auth())
    r = client.get("/api/v1/detection/reports", headers=_auth())
    assert len(r.json()) == 2


# ── 8.10 Analytics ──

def test_analytics():
    r = client.get("/api/v1/detection/analytics")
    assert r.status_code == 200
    data = r.json()
    assert "total_rules" in data
    assert "enabled_rules" in data
    assert "total_hits" in data
    assert "false_positive_rate" in data
    assert "by_category" in data
    assert "by_severity" in data
    assert "top_rules" in data
    assert "hunting_metrics" in data


def test_record_hit():
    r1 = client.post("/api/v1/detection/rules", json={"name": "Hit Counter"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/analytics/hit?rule_type=detection&rule_id={r1['id']}&event_source=test", headers=_auth())
    assert r.status_code == 200
    r = client.get(f"/api/v1/detection/rules/{r1['id']}")
    assert r.json()["hit_count"] == 1


# ── Edge Cases ──

def test_unauthorized_access():
    r = client.get("/api/v1/detection/hunts")
    assert r.status_code == 401
    r = client.post("/api/v1/detection/hunts", json={"name": "X"})
    assert r.status_code == 401


def test_hunt_results_no_data():
    r = client.get("/api/v1/detection/hunts/results", headers=_auth())
    assert r.status_code == 200
    assert r.json() == []


def test_analytics_with_no_rules():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp = f.name
    try:
        import src.config
        orig = src.config.settings.database_path
        src.config.settings.database_path = tmp
        init_db()
        r = client.get("/api/v1/detection/analytics")
        assert r.status_code == 200
        assert r.json()["total_rules"] == 0
        src.config.settings.database_path = orig
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def test_execute_hunt_custom():
    _upload_log()
    h = client.post("/api/v1/detection/hunts", json={"name": "Custom Hunt", "hunt_type": "custom", "query": "Failed"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/hunts/{h['id']}/execute", headers=_auth())
    assert r.status_code == 200
    assert r.json()["total_results"] >= 1


def test_process_hunt():
    _upload_log()
    h = client.post("/api/v1/detection/hunts", json={"name": "Proc Hunt", "hunt_type": "process", "query": "sshd"}, headers=_auth()).json()
    r = client.post(f"/api/v1/detection/hunts/{h['id']}/execute", headers=_auth())
    assert r.status_code == 200


def test_hunt_isolation():
    client.post("/api/v1/auth/register", json={"username": "other", "email": "b@b.com", "password": "pass"})
    r = client.post("/api/v1/auth/login", json={"username": "other", "password": "pass"})
    auth2 = {"Authorization": f"Bearer {r.json()['access_token']}"}
    h = client.post("/api/v1/detection/hunts", json={"name": "Private Hunt"}, headers=_auth()).json()
    r = client.get(f"/api/v1/detection/hunts/{h['id']}", headers=auth2)
    assert r.status_code == 404
    r = client.delete(f"/api/v1/detection/hunts/{h['id']}", headers=auth2)
    assert r.status_code == 404
