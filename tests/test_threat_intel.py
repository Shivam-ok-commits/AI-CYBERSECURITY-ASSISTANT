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
    monkeypatch.setattr("src.config.settings.virustotal_api_key", "")
    monkeypatch.setattr("src.config.settings.abuseipdb_api_key", "")
    monkeypatch.setattr("src.config.settings.otx_api_key", "")
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


# ── 4.1 IOC Extraction ──

def test_extract_iocs_from_text():
    r = client.post("/api/v1/threat/extract?text=Connection from 8.8.8.8 to evil.com (d41d8cd98f00b204e9800998ecf8427e) and user@evil.com http://malware.example.com/payload.exe")
    assert r.status_code == 200
    data = r.json()
    assert "8.8.8.8" in data["ips"]
    assert any("evil.com" in d for d in data["domains"])
    assert len(data["urls"]) > 0
    assert len(data["emails"]) > 0
    assert len(data["hashes"]) > 0


def test_extract_iocs_from_log():
    lid = _upload("Connection from 1.1.1.1 to malware.example.com (d41d8cd98f00b204e9800998ecf8427e)")
    r = client.get(f"/api/v1/threat/extract/{lid}", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_extract_ignores_private_ips():
    r = client.post("/api/v1/threat/extract?text=Connection from 192.168.1.1 and 10.0.0.1 to 8.8.8.8")
    data = r.json()
    assert "192.168.1.1" not in data["ips"]
    assert "10.0.0.1" not in data["ips"]
    assert "8.8.8.8" in data["ips"]


def test_extract_hashes():
    r = client.post("/api/v1/threat/extract?text=MD5: d41d8cd98f00b204e9800998ecf8427e SHA1: da39a3ee5e6b4b0d3255bfef95601890afd80709 SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
    data = r.json()
    assert len(data["hashes"]) == 3
    types = {h["type"] for h in data["hashes"]}
    assert types == {"md5", "sha1", "sha256"}


# ── 4.2 IOC Lookup ──

@pytest.mark.asyncio
async def test_lookup_ip():
    r = client.get("/api/v1/threat/lookup?indicator=8.8.8.8&type=ip")
    assert r.status_code == 200
    data = r.json()
    assert data["indicator"] == "8.8.8.8"
    assert data["indicator_type"] == "ip"
    assert "reputation" in data


@pytest.mark.asyncio
async def test_lookup_domain():
    r = client.get("/api/v1/threat/lookup?indicator=google.com&type=domain")
    assert r.status_code == 200
    assert r.json()["indicator"] == "google.com"


@pytest.mark.asyncio
async def test_lookup_hash():
    r = client.get("/api/v1/threat/lookup?indicator=d41d8cd98f00b204e9800998ecf8427e&type=md5")
    assert r.status_code == 200
    assert r.json()["indicator_type"] == "md5"


@pytest.mark.asyncio
async def test_lookup_invalid_type():
    r = client.get("/api/v1/threat/lookup?indicator=test&type=invalid")
    assert r.status_code == 400


# ── 4.5 IOC Dashboard ──

def test_list_iocs():
    client.get("/api/v1/threat/lookup?indicator=8.8.8.8&type=ip")
    client.get("/api/v1/threat/lookup?indicator=1.1.1.1&type=ip")
    r = client.get("/api/v1/threat/iocs", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) >= 2


def test_search_iocs():
    client.get("/api/v1/threat/lookup?indicator=8.8.8.8&type=ip")
    r = client.get("/api/v1/threat/iocs?q=8.8", headers=_auth())
    assert len(r.json()) >= 1
    r2 = client.get("/api/v1/threat/iocs?q=nonexistent", headers=_auth())
    assert len(r2.json()) == 0


def test_filter_iocs_by_type():
    client.get("/api/v1/threat/lookup?indicator=8.8.8.8&type=ip")
    client.get("/api/v1/threat/lookup?indicator=d41d8cd98f00b204e9800998ecf8427e&type=md5")
    r = client.get("/api/v1/threat/iocs?type=md5", headers=_auth())
    assert all(i["indicator_type"] == "md5" for i in r.json())


def test_ioc_detail():
    client.get("/api/v1/threat/lookup?indicator=8.8.8.8&type=ip")
    r = client.get("/api/v1/threat/iocs/8.8.8.8")
    assert r.status_code == 200
    assert r.json()["indicator"] == "8.8.8.8"


def test_ioc_detail_not_found():
    r = client.get("/api/v1/threat/iocs/999.999.999.999")
    assert r.status_code == 404


def test_ioc_stats():
    client.get("/api/v1/threat/lookup?indicator=8.8.8.8&type=ip")
    r = client.get("/api/v1/threat/iocs/stats", headers=_auth())
    assert r.status_code == 200
    assert r.json()["total_iocs"] >= 1


# ── 4.6 IOC Correlation ──

def test_correlate_no_iocs():
    lid = _upload("some benign text")
    r = client.get(f"/api/v1/threat/correlate/{lid}", headers=_auth())
    assert r.status_code == 404


def test_correlate_global():
    r = client.get("/api/v1/threat/correlate/global", headers=_auth())
    assert r.status_code == 200


# ── 4.7 Threat Feed ──

def test_threat_feed():
    r = client.get("/api/v1/threat/feed")
    assert r.status_code == 200
    data = r.json()
    assert "latest_malware" in data
    assert "latest_ransomware" in data
    assert "latest_threat_actors" in data


@pytest.mark.asyncio
async def test_daily_summary():
    r = client.get("/api/v1/threat/feed/daily")
    assert r.status_code == 200
    data = r.json()
    assert "date" in data


# ── 4.3 Intelligence Sources ──

@pytest.mark.asyncio
async def test_cisa_kev():
    r = client.get("/api/v1/threat/cisa-kev")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_cve_lookup():
    r = client.get("/api/v1/threat/cve/CVE-2024-99999")
    assert r.status_code in (200, 404)


# ── Unit tests ──

def test_extract_iocs_unit():
    from src.services.ioc_extractor import extract_iocs
    result = extract_iocs("File hash: d41d8cd98f00b204e9800998ecf8427e IP: 8.8.8.8 Domain: evil.com")
    assert "8.8.8.8" in result["ips"]
    assert len(result["hashes"]) == 1


def test_extract_from_events_unit():
    from src.services.ioc_extractor import extract_from_events
    rows = [{"raw": "Connection from 8.8.4.4 to malicious.com (cafef00dd1e54aaba4d1f5b7c3e1a2b3)", "log_id": 1, "line_number": 1}]
    results = extract_from_events(rows)
    assert len(results) >= 2
    assert "ip" in {r["indicator_type"] for r in results}


def test_correlate_iocs_unit():
    from src.services.ioc_correlation import correlate_iocs
    iocs = [
        {"indicator": "1.2.3.4", "indicator_type": "ip", "log_id": 1},
        {"indicator": "1.2.3.4", "indicator_type": "ip", "log_id": 2},
        {"indicator": "evil.com", "indicator_type": "domain", "log_id": 1},
    ]
    result = correlate_iocs(iocs)
    assert result["total_iocs"] == 2
    assert len(result["repeated_iocs"]) == 1
    assert result["repeated_iocs"][0]["indicator"] == "1.2.3.4"


def test_generate_threat_feed_unit():
    from src.services.threat_feed import generate_threat_feed
    feed = generate_threat_feed()
    assert len(feed["latest_malware"]) > 0
    assert len(feed["latest_ransomware"]) > 0
    assert len(feed["latest_threat_actors"]) > 0
