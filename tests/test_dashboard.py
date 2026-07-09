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


# ── 7.1 Executive Dashboard ──

def test_executive_summary():
    r = client.get("/api/v1/dashboard/executive")
    assert r.status_code == 200
    data = r.json()
    assert "risk_score" in data
    assert "security_health" in data
    assert "total_alerts" in data
    assert isinstance(data["risk_score"], float)


def test_full_dashboard():
    r = client.get("/api/v1/dashboard/summary", headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert "executive" in data
    assert "alerts" in data
    assert "investigations" in data
    assert "threat_intel" in data
    assert "log_stats" in data
    assert "notifications" in data


# ── 7.2 Alert Center ──

def test_create_alert():
    r = client.post("/api/v1/dashboard/alerts", json={"title": "Suspicious Login", "severity": "high", "alert_type": "anomaly"}, headers=_auth())
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Suspicious Login"
    assert data["severity"] == "high"
    assert data["status"] == "open"


def test_create_alert_with_all_fields():
    r = client.post("/api/v1/dashboard/alerts", json={
        "title": "Malware Detected",
        "description": "EICAR test file detected on endpoint",
        "severity": "critical",
        "alert_type": "malware",
        "source": "EDR",
        "assigned_to": "jane",
        "ioc_value": "eicar.com",
        "event_count": 3,
    }, headers=_auth())
    assert r.status_code == 201
    assert r.json()["ioc_value"] == "eicar.com"
    assert r.json()["event_count"] == 3


def test_list_alerts():
    client.post("/api/v1/dashboard/alerts", json={"title": "A1", "severity": "low"}, headers=_auth())
    client.post("/api/v1/dashboard/alerts", json={"title": "A2", "severity": "high"}, headers=_auth())
    r = client.get("/api/v1/dashboard/alerts")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_filter_alerts_by_severity():
    client.post("/api/v1/dashboard/alerts", json={"title": "Low", "severity": "low"}, headers=_auth())
    client.post("/api/v1/dashboard/alerts", json={"title": "Critical", "severity": "critical"}, headers=_auth())
    r = client.get("/api/v1/dashboard/alerts?severity=critical")
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "Critical"


def test_filter_alerts_by_status():
    a = client.post("/api/v1/dashboard/alerts", json={"title": "Resolve Me"}, headers=_auth()).json()
    client.put(f"/api/v1/dashboard/alerts/{a['id']}", json={"status": "resolved"}, headers=_auth())
    r = client.get("/api/v1/dashboard/alerts?status=resolved")
    assert len(r.json()) == 1


def test_filter_alerts_by_type():
    client.post("/api/v1/dashboard/alerts", json={"title": "Phish", "alert_type": "phishing"}, headers=_auth())
    r = client.get("/api/v1/dashboard/alerts?alert_type=phishing")
    assert len(r.json()) == 1


def test_search_alerts():
    client.post("/api/v1/dashboard/alerts", json={"title": "Find Me Please"}, headers=_auth())
    r = client.get("/api/v1/dashboard/alerts?query=Find")
    assert len(r.json()) == 1


def test_get_alert():
    a = client.post("/api/v1/dashboard/alerts", json={"title": "Get Me"}, headers=_auth()).json()
    r = client.get(f"/api/v1/dashboard/alerts/{a['id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Get Me"


def test_get_alert_not_found():
    r = client.get("/api/v1/dashboard/alerts/9999")
    assert r.status_code == 404


def test_update_alert():
    a = client.post("/api/v1/dashboard/alerts", json={"title": "Old Title"}, headers=_auth()).json()
    r = client.put(f"/api/v1/dashboard/alerts/{a['id']}", json={"title": "New Title", "severity": "critical"}, headers=_auth())
    assert r.status_code == 200
    assert r.json()["title"] == "New Title"
    assert r.json()["severity"] == "critical"


def test_update_alert_not_found():
    r = client.put("/api/v1/dashboard/alerts/9999", json={"title": "Nope"}, headers=_auth())
    assert r.status_code == 404


def test_alert_stats():
    client.post("/api/v1/dashboard/alerts", json={"title": "S1", "severity": "high"}, headers=_auth())
    client.post("/api/v1/dashboard/alerts", json={"title": "S2", "severity": "critical"}, headers=_auth())
    r = client.get("/api/v1/dashboard/alerts/stats")
    assert r.status_code == 200
    assert r.json()["total"] >= 2
    assert "by_severity" in r.json()
    assert "by_status" in r.json()
    assert "by_type" in r.json()


def test_update_alert_resolve_sets_timestamp():
    a = client.post("/api/v1/dashboard/alerts", json={"title": "Resolve"}, headers=_auth()).json()
    r = client.put(f"/api/v1/dashboard/alerts/{a['id']}", json={"status": "resolved"}, headers=_auth())
    assert r.json()["resolved_at"] is not None


# ── 7.5 Asset Dashboard ──

def test_create_asset():
    r = client.post("/api/v1/dashboard/assets", json={"hostname": "web-01", "ip_address": "10.0.0.1", "asset_type": "server", "risk_score": 8.5, "criticality": "high"})
    assert r.status_code == 201
    assert r.json()["hostname"] == "web-01"
    assert r.json()["ip_address"] == "10.0.0.1"


def test_create_asset_minimal():
    r = client.post("/api/v1/dashboard/assets", json={"hostname": "test-host"})
    assert r.status_code == 201
    assert r.json()["asset_type"] == "host"


def test_list_assets():
    client.post("/api/v1/dashboard/assets", json={"hostname": "A", "criticality": "critical"})
    client.post("/api/v1/dashboard/assets", json={"hostname": "B", "criticality": "low"})
    r = client.get("/api/v1/dashboard/assets")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_filter_assets_by_criticality():
    client.post("/api/v1/dashboard/assets", json={"hostname": "Critical-Srv", "criticality": "critical"})
    client.post("/api/v1/dashboard/assets", json={"hostname": "Low-Srv", "criticality": "low"})
    r = client.get("/api/v1/dashboard/assets?criticality=critical")
    assert len(r.json()) == 1


def test_filter_assets_by_type():
    client.post("/api/v1/dashboard/assets", json={"hostname": "DB", "asset_type": "database"})
    r = client.get("/api/v1/dashboard/assets?asset_type=database")
    assert len(r.json()) == 1


def test_search_assets():
    client.post("/api/v1/dashboard/assets", json={"hostname": "mail-server"})
    r = client.get("/api/v1/dashboard/assets?query=mail")
    assert len(r.json()) == 1


def test_get_asset():
    a = client.post("/api/v1/dashboard/assets", json={"hostname": "Get-Me"}).json()
    r = client.get(f"/api/v1/dashboard/assets/{a['id']}")
    assert r.status_code == 200
    assert r.json()["hostname"] == "Get-Me"


def test_get_asset_not_found():
    r = client.get("/api/v1/dashboard/assets/9999")
    assert r.status_code == 404


def test_update_asset():
    a = client.post("/api/v1/dashboard/assets", json={"hostname": "Old", "risk_score": 3.0}).json()
    r = client.put(f"/api/v1/dashboard/assets/{a['id']}", json={"hostname": "New", "risk_score": 9.5})
    assert r.status_code == 200
    assert r.json()["hostname"] == "New"
    assert r.json()["risk_score"] == 9.5


def test_update_asset_not_found():
    r = client.put("/api/v1/dashboard/assets/9999", json={"hostname": "X"})
    assert r.status_code == 404


def test_delete_asset():
    a = client.post("/api/v1/dashboard/assets", json={"hostname": "Delete-Me"}).json()
    r = client.delete(f"/api/v1/dashboard/assets/{a['id']}")
    assert r.status_code == 204
    r = client.get(f"/api/v1/dashboard/assets/{a['id']}")
    assert r.status_code == 404


def test_delete_asset_not_found():
    r = client.delete("/api/v1/dashboard/assets/9999")
    assert r.status_code == 404


# ── 7.3 Investigation Dashboard ──

def test_investigation_stats():
    r = client.get("/api/v1/dashboard/investigations/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "open" in data
    assert "closed" in data
    assert "by_severity" in data
    assert "avg_resolution_time" in data


# ── 7.4 Threat Intelligence Dashboard ──

def test_threat_intel_stats():
    r = client.get("/api/v1/dashboard/threat/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_iocs" in data
    assert "by_type" in data
    assert "top_threats" in data


# ── 7.6 Log Monitoring ──

def test_log_stats():
    r = client.get("/api/v1/dashboard/logs/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_events" in data
    assert "by_severity" in data
    assert "by_event_type" in data
    assert "top_source_ips" in data
    assert "recent_activity" in data


# ── 7.7 Visual Analytics ──

def test_severity_chart():
    r = client.get("/api/v1/dashboard/charts/severity")
    assert r.status_code == 200
    data = r.json()
    assert "labels" in data
    assert "datasets" in data


def test_attack_timeline_chart():
    r = client.get("/api/v1/dashboard/charts/attack-timeline?days=7")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_threat_distribution():
    r = client.get("/api/v1/dashboard/charts/threat-distribution")
    assert r.status_code == 200
    assert "labels" in r.json()
    assert "values" in r.json()


def test_ioc_trend():
    r = client.get("/api/v1/dashboard/charts/ioc-trend?days=30")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_cve_trend():
    r = client.get("/api/v1/dashboard/charts/cve-trend?days=30")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_event_type_chart():
    r = client.get("/api/v1/dashboard/charts/event-types")
    assert r.status_code == 200
    assert "labels" in r.json()
    assert "values" in r.json()


# ── 7.9 Notifications ──

def test_create_notification():
    r = client.post("/api/v1/dashboard/notifications", json={"title": "Critical Alert", "message": "Something happened", "severity": "high"}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["title"] == "Critical Alert"
    assert r.json()["is_read"] is False


def test_list_notifications():
    client.post("/api/v1/dashboard/notifications", json={"title": "N1"}, headers=_auth())
    client.post("/api/v1/dashboard/notifications", json={"title": "N2"}, headers=_auth())
    r = client.get("/api/v1/dashboard/notifications", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_unread_count():
    client.post("/api/v1/dashboard/notifications", json={"title": "Unread"}, headers=_auth())
    r = client.get("/api/v1/dashboard/notifications/unread-count", headers=_auth())
    assert r.status_code == 200
    assert r.json()["count"] >= 1


def test_mark_notification_read():
    n = client.post("/api/v1/dashboard/notifications", json={"title": "Read Me"}, headers=_auth()).json()
    r = client.post(f"/api/v1/dashboard/notifications/{n['id']}/read", headers=_auth())
    assert r.status_code == 200
    r = client.get("/api/v1/dashboard/notifications/unread-count", headers=_auth())
    assert r.json()["count"] == 0


def test_mark_notification_read_not_found():
    r = client.post("/api/v1/dashboard/notifications/9999/read", headers=_auth())
    assert r.status_code == 404


def test_mark_all_read():
    client.post("/api/v1/dashboard/notifications", json={"title": "A"}, headers=_auth())
    client.post("/api/v1/dashboard/notifications", json={"title": "B"}, headers=_auth())
    r = client.post("/api/v1/dashboard/notifications/read-all", headers=_auth())
    assert r.status_code == 200
    assert r.json()["marked"] >= 2
    r = client.get("/api/v1/dashboard/notifications/unread-count", headers=_auth())
    assert r.json()["count"] == 0


def test_filter_notifications_by_type():
    client.post("/api/v1/dashboard/notifications", json={"title": "Alert!", "notification_type": "alert"}, headers=_auth())
    client.post("/api/v1/dashboard/notifications", json={"title": "Info", "notification_type": "info"}, headers=_auth())
    r = client.get("/api/v1/dashboard/notifications?notif_type=alert", headers=_auth())
    assert len(r.json()) == 1


def test_unread_only_filter():
    n = client.post("/api/v1/dashboard/notifications", json={"title": "Read This"}, headers=_auth()).json()
    client.post(f"/api/v1/dashboard/notifications/{n['id']}/read", headers=_auth())
    client.post("/api/v1/dashboard/notifications", json={"title": "Still Unread"}, headers=_auth())
    r = client.get("/api/v1/dashboard/notifications?unread_only=true", headers=_auth())
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "Still Unread"


# ── 7.11 Settings ──

def test_get_settings():
    r = client.get("/api/v1/dashboard/settings", headers=_auth())
    assert r.status_code == 200
    assert "preferences" in r.json()
    assert "notification_config" in r.json()
    assert "dashboard_layout" in r.json()


def test_update_settings():
    r = client.put("/api/v1/dashboard/settings", json={"preferences": '{"theme": "dark"}'}, headers=_auth())
    assert r.status_code == 200
    assert '"theme": "dark"' in r.json()["preferences"]


def test_update_settings_partial():
    r = client.put("/api/v1/dashboard/settings", json={"dashboard_layout": '{"widgets": ["alerts","threats"]}'}, headers=_auth())
    assert r.status_code == 200
    assert "widgets" in r.json()["dashboard_layout"]


# ── 7.10 User Management ──

def test_list_analysts():
    r = client.get("/api/v1/dashboard/users/analysts", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) >= 1
    assert r.json()[0]["username"] == "analyst"


def test_user_activity():
    client.post("/api/v1/cases", json={"title": "Auditable Case"}, headers=_auth())
    r = client.get("/api/v1/dashboard/users/activity", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ── Edge Cases ──

def test_unauthorized_access():
    r = client.get("/api/v1/dashboard/summary")
    assert r.status_code == 401
    r = client.get("/api/v1/dashboard/notifications")
    assert r.status_code == 401


def test_empty_alert_stats():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp = f.name
    try:
        import src.config
        original = src.config.settings.database_path
        src.config.settings.database_path = tmp
        init_db()
        # Don't create any alerts
        r = client.get("/api/v1/dashboard/alerts/stats")
        assert r.status_code == 200
        assert r.json()["total"] == 0
        src.config.settings.database_path = original
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def test_charts_with_no_data():
    r = client.get("/api/v1/dashboard/charts/severity")
    assert r.status_code == 200
    r = client.get("/api/v1/dashboard/charts/threat-distribution")
    assert r.status_code == 200


def test_notifications_isolated_per_user():
    client.post("/api/v1/auth/register", json={"username": "user2", "email": "u2@u.com", "password": "pass"})
    r2 = client.post("/api/v1/auth/login", json={"username": "user2", "password": "pass"})
    auth2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}
    client.post("/api/v1/dashboard/notifications", json={"title": "User1 Notif"}, headers=_auth())
    client.post("/api/v1/dashboard/notifications", json={"title": "User2 Notif"}, headers=auth2)
    r = client.get("/api/v1/dashboard/notifications", headers=auth2)
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "User2 Notif"
