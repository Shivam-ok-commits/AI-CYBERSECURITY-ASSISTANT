import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.database import get_db, init_db
from src.services.ai_memory import get_session
from src.services.ai_rag import index_log_content, search_documents

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    tmp_db = tempfile.mktemp(suffix=".db")
    monkeypatch.setattr("src.config.settings.database_path", tmp_db)
    monkeypatch.setattr("src.config.settings.uploads_dir", tempfile.mkdtemp())
    monkeypatch.setattr("src.config.settings.openai_api_key", "")
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
    log += b"Sep 26 10:00:01 server sshd[1234]: Failed password for root from 10.0.0.1 port 22\n"
    log += b"Sep 26 10:00:02 server sshd[1234]: Accepted password for root from 10.0.0.1 port 22\n"
    r = client.post("/api/v1/logs/upload", files={"file": ("auth.log", log, "text/plain")}, headers=_auth())
    return r.json()["id"]


# ── 5.1 Chat Sessions ──

def test_create_session():
    r = client.post("/api/v1/ai/sessions", json={"title": "Test Session", "context_type": "general"}, headers=_auth())
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "Test Session"
    assert "id" in data
    assert data["context_type"] == "general"


def test_create_session_defaults():
    r = client.post("/api/v1/ai/sessions", json={}, headers=_auth())
    assert r.status_code == 201
    assert r.json()["title"] == "New Chat"


def test_list_sessions():
    client.post("/api/v1/ai/sessions", json={"title": "S1"}, headers=_auth())
    client.post("/api/v1/ai/sessions", json={"title": "S2"}, headers=_auth())
    r = client.get("/api/v1/ai/sessions", headers=_auth())
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_session():
    c = client.post("/api/v1/ai/sessions", json={"title": "My Session"}, headers=_auth()).json()
    r = client.get(f"/api/v1/ai/sessions/{c['id']}", headers=_auth())
    assert r.status_code == 200
    assert r.json()["title"] == "My Session"


def test_get_session_not_found():
    r = client.get("/api/v1/ai/sessions/9999", headers=_auth())
    assert r.status_code == 404


def test_get_session_history_empty():
    c = client.post("/api/v1/ai/sessions", json={}, headers=_auth()).json()
    r = client.get(f"/api/v1/ai/sessions/{c['id']}/history", headers=_auth())
    assert r.status_code == 200
    assert r.json() == []


def test_get_session_history_not_found():
    r = client.get("/api/v1/ai/sessions/9999/history", headers=_auth())
    assert r.status_code == 404


# ── 5.2 Chat ──

def test_chat_basic():
    c = client.post("/api/v1/ai/sessions", json={"title": "Chat"}, headers=_auth()).json()
    r = client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": "Hello"}, headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == c["id"]
    assert data["reply"]
    assert isinstance(data["suggested_questions"], list)
    assert isinstance(data["evidence"], list)
    assert isinstance(data["confidence"], float)


def test_chat_session_not_found():
    r = client.post("/api/v1/ai/chat", json={"session_id": 9999, "message": "Hello"}, headers=_auth())
    assert r.status_code == 404


def test_chat_saves_history():
    c = client.post("/api/v1/ai/sessions", json={}, headers=_auth()).json()
    client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": "Hello"}, headers=_auth())
    client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": "Explain Event ID 4625"}, headers=_auth())
    hist = client.get(f"/api/v1/ai/sessions/{c['id']}/history", headers=_auth())
    assert len(hist.json()) == 4
    roles = [m["role"] for m in hist.json()]
    assert roles == ["user", "assistant", "user", "assistant"]


# ── 5.3 Explain ──

def test_explain_windows_event_id():
    r = client.post("/api/v1/ai/explain", json={"text": "Event ID 4625"})
    assert r.status_code == 200
    assert "4625" in r.json()["explanation"]


def test_explain_linux_event():
    r = client.post("/api/v1/ai/explain", json={"text": "Failed password for root"})
    assert r.status_code == 200
    assert r.json()["explanation"]


def test_explain_powershell():
    r = client.post("/api/v1/ai/explain", json={"text": "PowerShell -EncodedCommand"})
    assert r.status_code == 200
    assert r.json()["explanation"]


def test_explain_generic():
    r = client.post("/api/v1/ai/explain", json={"text": "Unknown event XYZ"})
    assert r.status_code == 200
    assert r.json()["explanation"]


# ── 5.4 Log Investigation ──

def test_investigate_log():
    log_id = _upload_log()
    r = client.post("/api/v1/ai/investigate", json={"log_id": log_id}, headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]
    assert isinstance(data["suspicious_patterns"], list)
    assert isinstance(data["critical_events"], list)
    assert isinstance(data["attack_chain"], list)
    assert isinstance(data["priorities"], list)
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["confidence"], float)


def test_investigate_log_not_found():
    r = client.post("/api/v1/ai/investigate", json={"log_id": 9999}, headers=_auth())
    assert r.status_code == 404


def test_investigate_log_empty():
    log_id = _upload_log()
    with get_db() as conn:
        conn.execute("DELETE FROM parsed_events")
    r = client.post("/api/v1/ai/investigate", json={"log_id": log_id}, headers=_auth())
    assert r.status_code == 404


# ── 5.5 Recommendations ──

def test_recommendations():
    log_id = _upload_log()
    r = client.post("/api/v1/ai/recommendations", json={"log_id": log_id}, headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["next_steps"], list)
    assert isinstance(data["containment"], list)
    assert isinstance(data["recovery"], list)
    assert isinstance(data["patching"], list)
    assert isinstance(data["detection_improvements"], list)


def test_recommendations_not_found():
    r = client.post("/api/v1/ai/recommendations", json={"log_id": 9999}, headers=_auth())
    assert r.status_code == 404


# ── 5.6 Timeline Analysis ──

def test_timeline_analysis():
    log_id = _upload_log()
    r = client.post("/api/v1/ai/timeline", json={"log_id": log_id}, headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["timeline"], list)
    assert isinstance(data["attack_stages"], list)
    assert isinstance(data["root_cause"], str)
    assert isinstance(data["confidence"], float)


def test_timeline_analysis_not_found():
    r = client.post("/api/v1/ai/timeline", json={"log_id": 9999}, headers=_auth())
    assert r.status_code == 404


# ── 5.7 Interactive Q&A (ask) ──

def test_ask():
    c = client.post("/api/v1/ai/sessions", json={}, headers=_auth()).json()
    r = client.post("/api/v1/ai/ask", json={"session_id": c["id"], "message": "What should I investigate?"}, headers=_auth())
    assert r.status_code == 200
    data = r.json()
    assert data["session_id"] == c["id"]
    assert data["reply"]
    assert data["suggested_questions"]


def test_ask_session_not_found():
    r = client.post("/api/v1/ai/ask", json={"session_id": 9999, "message": "Hi"}, headers=_auth())
    assert r.status_code == 404


# ── 5.8 Evidence Linking (via chat) ──

def test_chat_evidence():
    c = client.post("/api/v1/ai/sessions", json={"context_type": "log", "context_id": 1}, headers=_auth()).json()
    r = client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": "Analyze 10.0.0.1"}, headers=_auth())
    assert r.status_code == 200
    data = r.json()
    if data["evidence"]:
        assert "type" in data["evidence"][0]
        assert "summary" in data["evidence"][0]


# ── 5.9 Prompts ──

def test_list_prompts():
    r = client.get("/api/v1/ai/prompts")
    assert r.status_code == 200
    assert len(r.json()) >= 4


def test_get_prompt():
    r = client.get("/api/v1/ai/prompts/system")
    assert r.status_code == 200
    assert r.json()["name"] == "system"
    assert r.json()["content"]


def test_get_prompt_not_found():
    r = client.get("/api/v1/ai/prompts/nonexistent")
    assert r.status_code == 200
    assert r.json()["name"] == "nonexistent"
    assert r.json()["content"]


# ── 5.10 RAG ──

def test_rag_search_no_results():
    r = client.post("/api/v1/ai/rag/search?query=malware")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["results"] == []


def test_rag_index_log_and_search():
    log_id = _upload_log()
    r = client.post(f"/api/v1/ai/rag/index/log/{log_id}", headers=_auth())
    assert r.status_code == 200
    assert r.json()["indexed"] is True
    assert r.json()["chunks"] > 0

    r = client.post("/api/v1/ai/rag/search?query=10.0.0.1")
    assert r.status_code == 200
    assert r.json()["total"] > 0


def test_rag_index_log_not_found():
    r = client.post("/api/v1/ai/rag/index/log/9999", headers=_auth())
    assert r.status_code == 404


# ── 5.11 Cross-Phase Integration ──

def test_investigate_with_rag():
    log_id = _upload_log()
    c = client.post("/api/v1/ai/sessions", json={"context_type": "log", "context_id": log_id}, headers=_auth()).json()

    client.post(f"/api/v1/ai/rag/index/log/{log_id}", headers=_auth())

    r = client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": "What happened with 10.0.0.1?"}, headers=_auth())
    assert r.status_code == 200
    assert r.json()["reply"]


def test_explain_after_investigation():
    r = client.post("/api/v1/ai/explain", json={"text": "What does CVE-2021-44228 mean?"})
    assert r.status_code == 200
    data = r.json()
    assert data["explanation"]
    assert isinstance(data["confidence"], float)


# ── 5.12 Edge Cases ──

def test_empty_chat_message():
    c = client.post("/api/v1/ai/sessions", json={}, headers=_auth()).json()
    r = client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": ""}, headers=_auth())
    assert r.status_code == 200
    assert r.json()["reply"]


def test_long_chat_message():
    long_msg = "Hello " * 1000
    c = client.post("/api/v1/ai/sessions", json={}, headers=_auth()).json()
    r = client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": long_msg}, headers=_auth())
    assert r.status_code == 200


def test_chat_help():
    c = client.post("/api/v1/ai/sessions", json={}, headers=_auth()).json()
    r = client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": "help"}, headers=_auth())
    assert r.status_code == 200
    assert "help" in r.json()["reply"].lower()


def test_chat_greeting():
    c = client.post("/api/v1/ai/sessions", json={}, headers=_auth()).json()
    r = client.post("/api/v1/ai/chat", json={"session_id": c["id"], "message": "hello"}, headers=_auth())
    assert r.status_code == 200
    assert "hello" in r.json()["reply"].lower()


def test_rag_filter_by_source_type():
    log_id = _upload_log()
    client.post(f"/api/v1/ai/rag/index/log/{log_id}", headers=_auth())
    r = client.post("/api/v1/ai/rag/search?query=10.0.0.1&source_type=log")
    assert r.status_code == 200


def test_multiple_sessions_isolation():
    a = client.post("/api/v1/ai/sessions", json={"title": "A"}, headers=_auth()).json()
    b = client.post("/api/v1/ai/sessions", json={"title": "B"}, headers=_auth()).json()

    client.post("/api/v1/ai/chat", json={"session_id": a["id"], "message": "Only in A"}, headers=_auth())
    client.post("/api/v1/ai/chat", json={"session_id": b["id"], "message": "Only in B"}, headers=_auth())

    ha = client.get(f"/api/v1/ai/sessions/{a['id']}/history", headers=_auth()).json()
    hb = client.get(f"/api/v1/ai/sessions/{b['id']}/history", headers=_auth()).json()

    assert len(ha) == 2
    assert len(hb) == 2
    assert any("Only in A" in m["content"] for m in ha)
    assert any("Only in B" in m["content"] for m in hb)
    assert not any("Only in B" in m["content"] for m in ha)


def test_unauthorized_access():
    r = client.get("/api/v1/ai/sessions")
    assert r.status_code == 401
    r = client.post("/api/v1/ai/chat", json={"session_id": 1, "message": "hi"})
    assert r.status_code == 401


def test_different_user_cannot_access():
    c = client.post("/api/v1/ai/sessions", json={}, headers=_auth()).json()
    sid = c["id"]
    client.post("/api/v1/auth/register", json={"username": "other", "email": "b@b.com", "password": "pass"})
    r = client.post("/api/v1/auth/login", json={"username": "other", "password": "pass"})
    other_auth = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.get(f"/api/v1/ai/sessions/{sid}", headers=other_auth)
    assert r.status_code == 404
    r = client.post("/api/v1/ai/chat", json={"session_id": sid, "message": "hi"}, headers=other_auth)
    assert r.status_code == 404


def test_rag_direct_index():
    events = [
        {"line_number": 1, "raw": "EVIL_MALWARE process started", "event_type": "process_creation", "severity": "high", "timestamp": "2024-01-01 00:00:00", "source_ip": "192.168.1.1"},
    ]
    index_log_content(999, events)
    results = search_documents("EVIL_MALWARE")
    assert len(results) >= 1
    assert "EVIL_MALWARE" in results[0]["chunk_text"]


def test_rag_search_with_source_filter():
    log_id = _upload_log()
    client.post(f"/api/v1/ai/rag/index/log/{log_id}", headers=_auth())
    results = search_documents("10.0.0.1", source_type="log")
    assert len(results) > 0
    results_wrong = search_documents("10.0.0.1", source_type="nonexistent")
    assert len(results_wrong) == 0
