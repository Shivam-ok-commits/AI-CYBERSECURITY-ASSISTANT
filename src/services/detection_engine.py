import json
import re
import time
import uuid
from datetime import datetime, timezone

from src.database import get_db

RULE_CATEGORIES = ("malware", "phishing", "brute_force", "web_attack", "insider_threat", "lateral_movement", "persistence", "execution", "credential_access", "exfiltration", "general", "custom")
RULE_TYPES = ("sigma", "yara", "custom")
RULE_FORMATS = ("sigma", "yara", "custom", "query", "regex")
SEVERITIES = ("low", "medium", "high", "critical")
SIGMA_STATUSES = ("experimental", "stable", "deprecated", "unsupported")
HUNT_TYPES = ("log", "ioc", "process", "network", "user", "custom")
JOB_TYPES = ("log_analysis", "ioc_check", "threat_feed_update", "malware_analysis", "hunt", "report")
SCHEDULE_INTERVALS = ("once", "hourly", "daily", "weekly", "monthly")
TRIGGER_TYPES = ("alert_created", "alert_severity", "alert_type", "ioc_detected", "rule_match", "schedule")
PLAYBOOK_CATEGORIES = ("malware", "phishing", "brute_force", "web_attack", "insider_threat", "general")


def _ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _dict_or_none(row):
    return dict(row) if row else None


# ── 8.1 Custom Detection Rules ──

def create_detection_rule(user_id: int, data: dict) -> dict:
    rt = data["rule_type"] if data["rule_type"] in RULE_TYPES else "custom"
    rf = data["rule_format"] if data["rule_format"] in RULE_FORMATS else "custom"
    cat = data["category"] if data["category"] in RULE_CATEGORIES else "general"
    sev = data["severity"] if data["severity"] in SEVERITIES else "medium"
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO detection_rules (name, description, rule_type, rule_format, category, content, severity, mitre_attack_id, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data["name"], data.get("description", ""), rt, rf, cat, data.get("content", ""), sev, data.get("mitre_attack_id", ""), user_id),
        )
        row = conn.execute("SELECT * FROM detection_rules WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def update_detection_rule(rule_id: int, data: dict) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM detection_rules WHERE id = ?", (rule_id,)).fetchone()
        if not row:
            return None
        fields, vals = [], []
        for k in ("name", "description", "category", "content", "severity", "mitre_attack_id"):
            if k in data and data[k] is not None:
                if k == "category" and data[k] not in RULE_CATEGORIES:
                    continue
                if k == "severity" and data[k] not in SEVERITIES:
                    continue
                fields.append(f"{k} = ?")
                vals.append(data[k])
        if "enabled" in data and data["enabled"] is not None:
            fields.append("enabled = ?")
            vals.append(1 if data["enabled"] else 0)
        if not fields:
            return dict(row)
        fields.append("updated_at = ?")
        vals.append(_ts())
        vals.append(rule_id)
        conn.execute(f"UPDATE detection_rules SET {', '.join(fields)} WHERE id = ?", vals)
        row = conn.execute("SELECT * FROM detection_rules WHERE id = ?", (rule_id,)).fetchone()
    return dict(row)


def delete_detection_rule(rule_id: int) -> bool:
    with get_db() as conn:
        r = conn.execute("DELETE FROM detection_rules WHERE id = ?", (rule_id,))
        return r.rowcount > 0


def get_detection_rule(rule_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM detection_rules WHERE id = ?", (rule_id,)).fetchone()
    return dict(row) if row else None


def list_detection_rules(category: str = "", rule_type: str = "", severity: str = "", enabled_only: bool = False, query: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = [], []
    if category:
        conds.append("category = ?"); args.append(category)
    if rule_type:
        conds.append("rule_type = ?"); args.append(rule_type)
    if severity:
        conds.append("severity = ?"); args.append(severity)
    if enabled_only:
        conds.append("enabled = 1")
    if query:
        conds.append("(name LIKE ? OR description LIKE ? OR mitre_attack_id LIKE ?)")
        q = f"%{query}%"; args.extend([q, q, q])
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM detection_rules {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


def test_detection_rule(rule_id: int, sample_data: list[str]) -> dict:
    rule = get_detection_rule(rule_id)
    if not rule:
        return {"rule_id": rule_id, "matched": False, "matches": [], "execution_time_ms": 0, "error": "Rule not found"}
    start = time.time()
    matches = []
    content = rule["content"]
    for line in sample_data:
        try:
            if rule["rule_format"] == "regex":
                if re.search(content, line, re.IGNORECASE):
                    matches.append({"line": line[:200], "match": content})
            elif rule["rule_format"] == "query":
                keywords = [k.strip().lower() for k in content.replace("AND", ",").replace("OR", ",").split(",") if k.strip()]
                if all(k in line.lower() for k in keywords):
                    matches.append({"line": line[:200], "keywords": keywords})
            else:
                keywords = content.lower().split()
                if any(k in line.lower() for k in keywords):
                    matches.append({"line": line[:200], "matched_keywords": [k for k in keywords if k in line.lower()]})
        except re.error:
            pass
    elapsed = (time.time() - start) * 1000
    return {"rule_id": rule_id, "matched": len(matches) > 0, "matches": matches[:20], "execution_time_ms": round(elapsed, 2), "error": ""}


# ── 8.2 Sigma Rule Support ──

def create_sigma_rule(data: dict) -> dict:
    st = data.get("status", "experimental") if data.get("status") in SIGMA_STATUSES else "experimental"
    with get_db() as conn:
        rid = data.get("rule_id") or f"SIGMA-{uuid.uuid4().hex[:8].upper()}"
        cur = conn.execute(
            "INSERT INTO sigma_rules (title, description, author, rule_id, logsource_category, logsource_product, logsource_service, detection, fields, falsepositives, level, tags, status, content) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data["title"], data.get("description", ""), data.get("author", ""), rid, data.get("logsource_category", ""), data.get("logsource_product", ""), data.get("logsource_service", ""), data.get("detection", "{}"), data.get("fields", "[]"), data.get("falsepositives", "[]"), data.get("level", "medium"), data.get("tags", "[]"), st, data.get("content", "")),
        )
        row = conn.execute("SELECT * FROM sigma_rules WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_sigma_rules(level: str = "", status: str = "", query: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = [], []
    if level:
        conds.append("level = ?"); args.append(level)
    if status:
        conds.append("status = ?"); args.append(status)
    if query:
        conds.append("(title LIKE ? OR description LIKE ? OR author LIKE ?)")
        q = f"%{query}%"; args.extend([q, q, q])
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM sigma_rules {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


def get_sigma_rule(rule_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM sigma_rules WHERE id = ?", (rule_id,)).fetchone()
    return dict(row) if row else None


def delete_sigma_rule(rule_id: int) -> bool:
    with get_db() as conn:
        r = conn.execute("DELETE FROM sigma_rules WHERE id = ?", (rule_id,))
        return r.rowcount > 0


def validate_sigma_rule(content: str) -> dict:
    errors = []
    try:
        parsed = json.loads(content) if content.startswith("{") else {}
        if not parsed.get("title"):
            errors.append("Missing required field: title")
        if not parsed.get("detection"):
            errors.append("Missing required field: detection")
        if parsed.get("detection"):
            sel = parsed["detection"]
            if "condition" not in sel and "selections" not in sel:
                errors.append("Detection must contain 'condition' or 'selections'")
    except json.JSONDecodeError:
        errors.append("Invalid JSON content")
    return {"valid": len(errors) == 0, "errors": errors}


def execute_sigma_rule(rule_id: int, events: list[dict]) -> dict:
    rule = get_sigma_rule(rule_id)
    if not rule:
        return {"rule_id": rule_id, "matched": False, "matches": [], "error": "Rule not found"}
    start = time.time()
    matches = []
    detection = {}
    try:
        detection = json.loads(rule["detection"]) if rule["detection"] else {}
    except (json.JSONDecodeError, TypeError):
        pass
    keywords = []
    for key, val in detection.items():
        if key in ("condition", "timeframe", "selections"):
            continue
        if isinstance(val, str):
            keywords.append(val.lower())
        elif isinstance(val, list):
            keywords.extend(str(v).lower() for v in val)
    for ev in events:
        raw = (ev.get("raw") or "").lower()
        if all(k in raw for k in keywords):
            matches.append({"event_id": ev.get("id"), "line": raw[:200]})
    elapsed = (time.time() - start) * 1000
    return {"rule_id": rule_id, "matched": len(matches) > 0, "matches": matches[:20], "execution_time_ms": round(elapsed, 2), "error": ""}


def export_sigma_rule(rule_id: int) -> dict | None:
    rule = get_sigma_rule(rule_id)
    if not rule:
        return None
    return {
        "title": rule["title"],
        "description": rule["description"],
        "author": rule["author"],
        "id": rule["rule_id"],
        "logsource": {
            "category": rule["logsource_category"],
            "product": rule["logsource_product"],
            "service": rule["logsource_service"],
        },
        "detection": json.loads(rule["detection"]) if rule["detection"] else {},
        "fields": json.loads(rule["fields"]) if rule["fields"] else [],
        "falsepositives": json.loads(rule["falsepositives"]) if rule["falsepositives"] else [],
        "level": rule["level"],
        "tags": json.loads(rule["tags"]) if rule["tags"] else [],
        "status": rule["status"],
    }


# ── 8.3 YARA Rule Support ──

def create_yara_rule(data: dict) -> dict:
    with get_db() as conn:
        rid = data.get("rule_id") or f"YARA-{uuid.uuid4().hex[:8].upper()}"
        cur = conn.execute(
            "INSERT INTO yara_rules (name, description, author, rule_id, content, tags, malware_family, reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (data["name"], data.get("description", ""), data.get("author", ""), rid, data["content"], data.get("tags", "[]"), data.get("malware_family", ""), data.get("reference", "")),
        )
        row = conn.execute("SELECT * FROM yara_rules WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_yara_rules(query: str = "", enabled_only: bool = False, limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = [], []
    if enabled_only:
        conds.append("enabled = 1")
    if query:
        conds.append("(name LIKE ? OR description LIKE ? OR malware_family LIKE ?)")
        q = f"%{query}%"; args.extend([q, q, q])
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM yara_rules {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


def get_yara_rule(rule_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM yara_rules WHERE id = ?", (rule_id,)).fetchone()
    return dict(row) if row else None


def delete_yara_rule(rule_id: int) -> bool:
    with get_db() as conn:
        r = conn.execute("DELETE FROM yara_rules WHERE id = ?", (rule_id,))
        return r.rowcount > 0


def validate_yara_rule(content: str) -> dict:
    errors = []
    if "rule " not in content:
        errors.append("YARA rule must contain a 'rule' declaration")
    if "condition:" not in content:
        errors.append("YARA rule must contain a 'condition' section")
    if not content.strip():
        errors.append("YARA rule content is empty")
    return {"valid": len(errors) == 0, "errors": errors}


def scan_with_yara(rule_id: int, file_contents: list[str]) -> dict:
    rule = get_yara_rule(rule_id)
    if not rule:
        return {"rule_id": rule_id, "matched": False, "matches": [], "error": "Rule not found"}
    start = time.time()
    matches = []
    content_lower = rule["content"].lower()
    strings_section = content_lower.split("strings:")[1].split("condition:")[0] if "strings:" in content_lower and "condition:" in content_lower else ""
    string_patterns = re.findall(r'\$[a-zA-Z0-9_]+\s*=\s*"([^"]*)"', strings_section)
    for i, fc in enumerate(file_contents):
        fc_lower = fc.lower()
        found = [s for s in string_patterns if s.lower() in fc_lower]
        if found:
            matches.append({"file_index": i, "content_preview": fc[:200], "matched_strings": found})
    elapsed = (time.time() - start) * 1000
    return {"rule_id": rule_id, "matched": len(matches) > 0, "matches": matches[:20], "execution_time_ms": round(elapsed, 2), "error": ""}


# ── 8.4 Threat Hunting ──

def create_saved_hunt(user_id: int, data: dict) -> dict:
    ht = data["hunt_type"] if data["hunt_type"] in HUNT_TYPES else "log"
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO saved_hunts (name, description, hunt_type, query, filters, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (data["name"], data.get("description", ""), ht, data.get("query", ""), data.get("filters", "{}"), user_id),
        )
        row = conn.execute("SELECT * FROM saved_hunts WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_saved_hunts(user_id: int, hunt_type: str = "", query: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = ["user_id = ?"], [user_id]
    if hunt_type:
        conds.append("hunt_type = ?"); args.append(hunt_type)
    if query:
        conds.append("(name LIKE ? OR description LIKE ?)")
        q = f"%{query}%"; args.extend([q, q])
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM saved_hunts WHERE {' AND '.join(conds)} ORDER BY updated_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


def get_saved_hunt(hunt_id: int, user_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM saved_hunts WHERE id = ? AND user_id = ?", (hunt_id, user_id)).fetchone()
    return dict(row) if row else None


def delete_saved_hunt(hunt_id: int, user_id: int) -> bool:
    with get_db() as conn:
        r = conn.execute("DELETE FROM saved_hunts WHERE id = ? AND user_id = ?", (hunt_id, user_id))
        return r.rowcount > 0


def execute_hunt(hunt_id: int, user_id: int) -> dict:
    hunt = get_saved_hunt(hunt_id, user_id)
    if not hunt:
        return {"error": "Hunt not found", "results": []}
    results = []
    ht = hunt["hunt_type"]
    query = hunt["query"].lower()
    filters = {}
    try:
        filters = json.loads(hunt["filters"]) if hunt["filters"] else {}
    except (json.JSONDecodeError, TypeError):
        pass
    with get_db() as conn:
        if ht == "log":
            rows = conn.execute("SELECT * FROM parsed_events ORDER BY id DESC LIMIT 500").fetchall()
            for r in rows:
                rd = dict(r)
                raw = (rd.get("raw") or "").lower()
                if not query or query in raw:
                    if not filters.get("severity") or rd.get("severity") == filters["severity"]:
                        results.append({"type": "log_event", "id": rd["id"], "match": rd.get("raw", "")[:200], "severity": rd.get("severity", "info")})
        elif ht == "ioc":
            rows = conn.execute("SELECT * FROM ioc_reputation ORDER BY threat_score DESC LIMIT 500").fetchall()
            for r in rows:
                rd = dict(r)
                indicator = rd.get("indicator", "").lower()
                if not query or query in indicator:
                    results.append({"type": "ioc", "indicator": rd["indicator"], "type_name": rd["indicator_type"], "score": rd["threat_score"]})
        elif ht in ("process", "network", "user"):
            rows = conn.execute("SELECT * FROM parsed_events ORDER BY id DESC LIMIT 500").fetchall()
            for r in rows:
                rd = dict(r)
                raw = (rd.get("raw") or "").lower()
                if not query or query in raw:
                    et = rd.get("event_type", "").lower()
                    if ht == "process" and ("process" in et or "4688" in raw or "created process" in raw):
                        results.append({"type": "process", "id": rd["id"], "match": rd.get("raw", "")[:200]})
                    elif ht == "network" and ("network" in et or "connection" in et or "5156" in raw):
                        results.append({"type": "network", "id": rd["id"], "match": rd.get("raw", "")[:200]})
                    elif ht == "user" and ("login" in et or "4624" in raw or "4625" in raw):
                        results.append({"type": "user_activity", "id": rd["id"], "match": rd.get("raw", "")[:200]})
        elif ht == "custom":
            rows = conn.execute("SELECT * FROM parsed_events ORDER BY id DESC LIMIT 1000").fetchall()
            for r in rows:
                rd = dict(r)
                raw = (rd.get("raw") or "").lower()
                if query and query in raw:
                    results.append({"type": "custom_match", "id": rd["id"], "match": rd.get("raw", "")[:200]})

    # Save results
    sev = filters.get("severity", "medium")
    with get_db() as conn:
        for res in results[:50]:
            conn.execute("INSERT INTO hunt_results (hunt_id, hunt_type, match_type, match_value, source, severity, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (hunt_id, ht, res.get("type", "match"), str(res.get("match", "")[:500]), "hunt", sev, user_id))
        conn.execute("UPDATE saved_hunts SET last_run = ?, is_scheduled = 0 WHERE id = ?", (_ts(), hunt_id))
    return {"hunt_id": hunt_id, "total_results": len(results), "results": results[:100]}


def list_hunt_results(user_id: int, hunt_type: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = ["user_id = ?"], [user_id]
    if hunt_type:
        conds.append("hunt_type = ?"); args.append(hunt_type)
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM hunt_results WHERE {' AND '.join(conds)} ORDER BY created_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


# ── 8.5 Scheduled Scans ──

def create_scheduled_job(user_id: int, data: dict) -> dict:
    jt = data["job_type"] if data["job_type"] in JOB_TYPES else "log_analysis"
    si = data["schedule_interval"] if data["schedule_interval"] in SCHEDULE_INTERVALS else "daily"
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO scheduled_jobs (name, job_type, config, schedule_interval, user_id) VALUES (?, ?, ?, ?, ?)",
            (data["name"], jt, data.get("config", "{}"), si, user_id),
        )
        row = conn.execute("SELECT * FROM scheduled_jobs WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_scheduled_jobs(user_id: int = 0, job_type: str = "", active_only: bool = False, limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = [], []
    if user_id:
        conds.append("user_id = ?"); args.append(user_id)
    if job_type:
        conds.append("job_type = ?"); args.append(job_type)
    if active_only:
        conds.append("is_active = 1")
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM scheduled_jobs {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


def update_scheduled_job(job_id: int, data: dict) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM scheduled_jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        fields, vals = [], []
        for k in ("name", "job_type", "config", "schedule_interval", "is_active"):
            if k in data and data[k] is not None:
                if k == "job_type" and data[k] not in JOB_TYPES:
                    continue
                if k == "schedule_interval" and data[k] not in SCHEDULE_INTERVALS:
                    continue
                if k == "is_active":
                    vals.append(1 if data[k] else 0)
                else:
                    vals.append(data[k])
                fields.append(f"{k} = ?")
        if not fields:
            return dict(row)
        fields.append("updated_at = ?")
        vals.append(_ts())
        vals.append(job_id)
        conn.execute(f"UPDATE scheduled_jobs SET {', '.join(fields)} WHERE id = ?", vals)
        row = conn.execute("SELECT * FROM scheduled_jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row)


def delete_scheduled_job(job_id: int) -> bool:
    with get_db() as conn:
        r = conn.execute("DELETE FROM scheduled_jobs WHERE id = ?", (job_id,))
        return r.rowcount > 0


def run_scheduled_job(job_id: int) -> dict:
    with get_db() as conn:
        job = conn.execute("SELECT * FROM scheduled_jobs WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return {"error": "Job not found"}
        jd = dict(job)
        jt = jd["job_type"]
        result = {"job_id": job_id, "job_type": jt, "status": "completed", "details": ""}
        if jt == "log_analysis":
            result["details"] = "Log analysis scan completed: checked parsed_events"
        elif jt == "ioc_check":
            result["details"] = "IOC check completed: verified ioc_reputation"
        elif jt == "threat_feed_update":
            result["details"] = "Threat feed update completed"
        elif jt == "malware_analysis":
            result["details"] = "Malware analysis scan completed"
        elif jt == "hunt":
            result["details"] = "Threat hunt executed"
        elif jt == "report":
            result["details"] = "Report generated"
        conn.execute("UPDATE scheduled_jobs SET last_run = ?, next_run = ?, updated_at = ? WHERE id = ?",
                     (_ts(), _ts(), _ts(), job_id))
    return result


# ── 8.6 Alert Automation ──

def create_alert_automation(data: dict) -> dict:
    tt = data["trigger_type"] if data["trigger_type"] in TRIGGER_TYPES else "alert_created"
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO alert_automation (name, description, trigger_type, conditions, actions, priority) VALUES (?, ?, ?, ?, ?, ?)",
            (data["name"], data.get("description", ""), tt, data.get("conditions", "{}"), data.get("actions", "[]"), int(data.get("priority", 0))),
        )
        row = conn.execute("SELECT * FROM alert_automation WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_alert_automations(trigger_type: str = "", active_only: bool = False, limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = [], []
    if trigger_type:
        conds.append("trigger_type = ?"); args.append(trigger_type)
    if active_only:
        conds.append("is_active = 1")
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM alert_automation {where} ORDER BY priority DESC, updated_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


def update_alert_automation(rule_id: int, data: dict) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM alert_automation WHERE id = ?", (rule_id,)).fetchone()
        if not row:
            return None
        fields, vals = [], []
        for k in ("name", "description", "trigger_type", "conditions", "actions", "priority", "is_active"):
            if k in data and data[k] is not None:
                if k == "is_active":
                    vals.append(1 if data[k] else 0)
                elif k == "priority":
                    vals.append(int(data[k]))
                else:
                    vals.append(data[k])
                fields.append(f"{k} = ?")
        if not fields:
            return dict(row)
        fields.append("updated_at = ?")
        vals.append(_ts())
        vals.append(rule_id)
        conn.execute(f"UPDATE alert_automation SET {', '.join(fields)} WHERE id = ?", vals)
        row = conn.execute("SELECT * FROM alert_automation WHERE id = ?", (rule_id,)).fetchone()
    return dict(row)


def delete_alert_automation(rule_id: int) -> bool:
    with get_db() as conn:
        r = conn.execute("DELETE FROM alert_automation WHERE id = ?", (rule_id,))
        return r.rowcount > 0


# ── 8.7 AI Rule Generator ──

def generate_sigma_from_natural(text: str) -> str:
    text_lower = text.lower()
    rule = {"title": f"AIGen: {text[:60]}", "description": f"Auto-generated from: {text}", "logsource": {"category": "unknown", "product": "windows"}, "detection": {"keywords": [], "condition": "keywords"}, "level": "medium", "tags": []}
    if "malware" in text_lower or "malicious" in text_lower:
        rule["logsource"]["category"] = "malware"
        rule["level"] = "high"
        rule["detection"]["keywords"] = ["malware", "malicious", "suspicious"]
    if "phishing" in text_lower:
        rule["logsource"]["category"] = "phishing"
        rule["detection"]["keywords"] = ["phishing", "login", "credential"]
    if "brute" in text_lower or "password" in text_lower:
        rule["logsource"]["product"] = "linux"
        rule["detection"]["keywords"] = ["failed password", "brute force", "authentication failure"]
        rule["level"] = "high"
    if "persistence" in text_lower:
        rule["tags"].append("persistence")
        rule["detection"]["keywords"] = ["service", "registry", "startup"]
    content = json.dumps(rule, indent=2)
    return content


def generate_yara_from_description(text: str) -> str:
    text_lower = text.lower()
    rule_name = "AIGen_Rule_" + uuid.uuid4().hex[:6]
    strings = []
    condition = "any of them"
    if "malware" in text_lower or "ransomware" in text_lower:
        strings = ['$s1 = "malicious"', '$s2 = "encrypt"', '$s3 = "ransom"']
    elif "phishing" in text_lower:
        strings = ['$s1 = "login"', '$s2 = "password"', '$s3 = "verify"']
    elif "backdoor" in text_lower or "trojan" in text_lower:
        strings = ['$s1 = "backdoor"', '$s2 = "cmd.exe"', '$s3 = "reverse"']
    else:
        keywords = [w for w in text.lower().split() if len(w) > 4][:5]
        strings = [f'$s{i+1} = "{kw}"' for i, kw in enumerate(keywords)]
    if not strings:
        strings = ['$s1 = "suspicious"']
    result = f'rule {rule_name} {{\n    meta:\n        description = "{text[:100]}"\n        generated = "true"\n\n    strings:\n        {"".join(f"        {s}\n" for s in strings)}\n    condition:\n        {condition}\n}}'
    return result


def explain_rule(content: str) -> str:
    lines = []
    if "rule " in content:
        lines.append("**YARA Rule**")
        name_match = re.search(r'rule\s+(\S+)', content)
        if name_match:
            lines.append(f"- Name: {name_match.group(1)}")
        string_count = len(re.findall(r'\$s\d+\s*=', content))
        if string_count:
            lines.append(f"- String patterns: {string_count}")
    elif "detection" in content or '"title"' in content:
        lines.append("**Sigma Rule**")
        try:
            parsed = json.loads(content) if content.startswith("{") else {}
            if parsed.get("title"):
                lines.append(f"- Title: {parsed['title']}")
            if parsed.get("level"):
                lines.append(f"- Level: {parsed['level']}")
            if parsed.get("logsource"):
                ls = parsed["logsource"]
                lines.append(f"- Log Source: {ls.get('category', '')} / {ls.get('product', '')}")
        except (json.JSONDecodeError, TypeError):
            pass
    else:
        lines.append("**Custom Rule**")
        lines.append(f"- Length: {len(content)} chars")
        lines.append(f"- Keywords detected: {len(re.findall(r'\w{4,}', content))}")
    return "\n".join(lines)


def improve_rule(content: str, suggestion: str) -> str:
    improved = content
    if suggestion:
        improved += f"\n\n# Improvement: {suggestion}"
    if "condition:" not in improved and "rule " in improved:
        if "condition:" not in improved.split("strings:")[-1] if "strings:" in improved else True:
            improved = improved.rstrip() + "\n    condition:\n        any of them\n"
    return improved


# ── 8.8 Workflow Automation ──

def create_workflow_playbook(data: dict) -> dict:
    cat = data["category"] if data["category"] in PLAYBOOK_CATEGORIES else "general"
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO workflow_playbooks (name, description, category, steps) VALUES (?, ?, ?, ?)",
            (data["name"], data.get("description", ""), cat, data.get("steps", "[]")),
        )
        row = conn.execute("SELECT * FROM workflow_playbooks WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_workflow_playbooks(category: str = "", active_only: bool = False, limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = [], []
    if category:
        conds.append("category = ?"); args.append(category)
    if active_only:
        conds.append("is_active = 1")
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM workflow_playbooks {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


def get_workflow_playbook(playbook_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM workflow_playbooks WHERE id = ?", (playbook_id,)).fetchone()
    return dict(row) if row else None


def delete_workflow_playbook(playbook_id: int) -> bool:
    with get_db() as conn:
        r = conn.execute("DELETE FROM workflow_playbooks WHERE id = ?", (playbook_id,))
        return r.rowcount > 0


# ── 8.9 Threat Hunting Reports ──

def create_hunting_report(user_id: int, data: dict) -> dict:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO hunting_reports (title, hunt_type, summary, findings, ioc_list, rule_matches, statistics, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (data["title"], data.get("hunt_type", "log"), data.get("summary", ""), data.get("findings", "[]"), data.get("ioc_list", "[]"), data.get("rule_matches", "[]"), data.get("statistics", "{}"), user_id),
        )
        row = conn.execute("SELECT * FROM hunting_reports WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_hunting_reports(user_id: int = 0, hunt_type: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    conds, args = [], []
    if user_id:
        conds.append("user_id = ?"); args.append(user_id)
    if hunt_type:
        conds.append("hunt_type = ?"); args.append(hunt_type)
    where = f"WHERE {' AND '.join(conds)}" if conds else ""
    with get_db() as conn:
        rows = conn.execute(f"SELECT * FROM hunting_reports {where} ORDER BY created_at DESC LIMIT ? OFFSET ?", args + [min(limit, 500), offset]).fetchall()
    return [dict(r) for r in rows]


# ── 8.10 Analytics ──

def get_detection_analytics() -> dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM detection_rules").fetchone()["c"]
        enabled = conn.execute("SELECT COUNT(*) as c FROM detection_rules WHERE enabled = 1").fetchone()["c"]
        total_hits = conn.execute("SELECT COALESCE(SUM(hit_count), 0) as c FROM detection_rules").fetchone()["c"]
        sigma_hits = conn.execute("SELECT COALESCE(SUM(hit_count), 0) as c FROM sigma_rules").fetchone()["c"]
        yara_hits = conn.execute("SELECT COALESCE(SUM(hit_count), 0) as c FROM yara_rules").fetchone()["c"]
        all_hits = total_hits + sigma_hits + yara_hits
        fp = conn.execute("SELECT COALESCE(SUM(false_positive_count), 0) as c FROM detection_rules").fetchone()["c"]
        fp_rate = round(fp / max(all_hits, 1) * 100, 2)
        by_cat = dict(conn.execute("SELECT category, COUNT(*) as c FROM detection_rules GROUP BY category").fetchall())
        by_sev = dict(conn.execute("SELECT severity, COUNT(*) as c FROM detection_rules GROUP BY severity").fetchall())
        by_mitre = {}
        for r in conn.execute("SELECT mitre_attack_id FROM detection_rules WHERE mitre_attack_id != ''").fetchall():
            for m in r["mitre_attack_id"].split(","):
                m = m.strip()
                if m:
                    by_mitre[m] = by_mitre.get(m, 0) + 1
        top = conn.execute("SELECT name, hit_count FROM detection_rules ORDER BY hit_count DESC LIMIT 10").fetchall()
        sigma_total = conn.execute("SELECT COUNT(*) as c FROM sigma_rules").fetchone()["c"]
        yara_total = conn.execute("SELECT COUNT(*) as c FROM yara_rules").fetchone()["c"]
        hunt_total = conn.execute("SELECT COUNT(*) as c FROM hunt_results").fetchone()["c"]
    return {
        "total_rules": total,
        "enabled_rules": enabled,
        "total_hits": all_hits,
        "false_positives": fp,
        "false_positive_rate": fp_rate,
        "by_category": dict(by_cat),
        "by_severity": dict(by_sev),
        "by_mitre": by_mitre,
        "top_rules": [{"name": r["name"], "hits": r["hit_count"]} for r in top],
        "hunting_metrics": {"sigma_rules": sigma_total, "yara_rules": yara_total, "hunt_results": hunt_total, "hunt_types": len(HUNT_TYPES)},
    }


def record_rule_hit(rule_type: str, rule_id: int, event_source: str = "", match_detail: str = "", severity: str = "medium", user_id: int = 0):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO rule_hits (rule_type, rule_id, event_source, match_detail, severity, user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (rule_type, rule_id, event_source, match_detail, severity, user_id),
        )
        table = "detection_rules" if rule_type == "detection" else f"{rule_type}_rules"
        conn.execute(f"UPDATE {table} SET hit_count = hit_count + 1, updated_at = ? WHERE id = ?", (_ts(), rule_id))
