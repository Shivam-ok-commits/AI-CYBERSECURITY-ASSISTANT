import json
import uuid
from datetime import datetime, timezone

from src.database import get_db

CASE_ID_PREFIX = "CASE-"
VALID_STATUSES = ("open", "in_progress", "closed")
VALID_SEVERITIES = ("low", "medium", "high", "critical")
VALID_TYPES = ("malware", "phishing", "brute_force", "web_attack", "insider_threat", "custom", "incident")
VALID_EVIDENCE_TYPES = ("file", "screenshot", "ioc", "malware_report", "log", "other")
VALID_REPORT_FORMATS = ("markdown", "html", "json", "pdf")

TEMPLATE_VARIABLES = (
    "executive_summary", "technical_summary", "attack_timeline", "ioc_list",
    "mitre_mapping", "root_cause", "impact_assessment", "containment_steps",
    "recovery_steps", "lessons_learned", "evidence_list", "source_ips",
    "affected_accounts", "affected_endpoints", "affected_users",
)


def _next_case_id() -> str:
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM cases").fetchone()
        return f"{CASE_ID_PREFIX}{row['cnt'] + 1:04d}"


def _log_activity(case_id: int, user_id: int, action: str, details: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO case_activity (case_id, user_id, action, details) VALUES (?, ?, ?, ?)",
            (case_id, user_id, action, details),
        )


def _audit_log(user_id: int, action: str, entity_type: str, entity_id: str = "", details: str = "", ip_address: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO audit_log (user_id, action, entity_type, entity_id, details, ip_address) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, action, entity_type, entity_id, details, ip_address),
        )


def _dict_or_none(row):
    return dict(row) if row else None


def _validate_case_access(case_id: int, user_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ? AND user_id = ?", (case_id, user_id)).fetchone()
    return dict(row) if row else None


# ── 6.3 Case Management ──

def create_case(title: str, user_id: int, description: str = "", case_type: str = "incident", severity: str = "medium", assigned_analyst: str = "") -> dict:
    case_type = case_type if case_type in VALID_TYPES else "incident"
    severity = severity if severity in VALID_SEVERITIES else "medium"
    case_id_val = _next_case_id()
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO cases (case_id, title, description, case_type, severity, user_id, assigned_analyst)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (case_id_val, title, description, case_type, severity, user_id, assigned_analyst),
        )
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (cur.lastrowid,)).fetchone()
    _log_activity(cur.lastrowid, user_id, "case_created", f"Case {case_id_val} created")
    _audit_log(user_id, "create", "case", case_id_val, f"Created case: {title}")
    return dict(row)


def get_case(case_id: int, user_id: int) -> dict | None:
    return _validate_case_access(case_id, user_id)


def list_cases(user_id: int, is_archived: bool = False, limit: int = 50, offset: int = 0) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, case_id, title, status, severity, case_type, assigned_analyst,
                      is_archived, created_at, updated_at
               FROM cases WHERE user_id = ? AND is_archived = ?
               ORDER BY updated_at DESC LIMIT ? OFFSET ?""",
            (user_id, 1 if is_archived else 0, limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def update_case(case_id: int, user_id: int, updates: dict) -> dict | None:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return None
    allowed = ("title", "description", "status", "severity", "case_type", "assigned_analyst",
               "findings", "root_cause", "impact_assessment", "containment_steps",
               "recovery_steps", "lessons_learned", "is_archived")
    fields = []
    vals = []
    for k, v in updates.items():
        if k in allowed and v is not None:
            if k == "status":
                v = v if v in VALID_STATUSES else case["status"]
            if k == "severity":
                v = v if v in VALID_SEVERITIES else case["severity"]
            fields.append(f"{k} = ?")
            vals.append(v)
    if not fields:
        return case
    fields.append("updated_at = datetime('now')")
    if updates.get("status") == "closed":
        fields.append("closed_at = datetime('now')")
    vals.append(case_id)
    with get_db() as conn:
        conn.execute(f"UPDATE cases SET {', '.join(fields)} WHERE id = ?", vals)
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    changed = [f for f in updates if f in allowed and updates[f] is not None]
    if changed:
        _log_activity(case_id, user_id, "case_updated", f"Updated: {', '.join(changed)}")
        _audit_log(user_id, "update", "case", case["case_id"], f"Updated fields: {', '.join(changed)}")
    return dict(row)


def archive_case(case_id: int, user_id: int) -> dict | None:
    return update_case(case_id, user_id, {"is_archived": True})


def delete_case(case_id: int, user_id: int) -> bool:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return False
    with get_db() as conn:
        conn.execute("DELETE FROM case_activity WHERE case_id = ?", (case_id,))
        conn.execute("DELETE FROM case_evidence WHERE case_id = ?", (case_id,))
        conn.execute("DELETE FROM case_comments WHERE case_id = ?", (case_id,))
        conn.execute("DELETE FROM case_reports WHERE case_id = ?", (case_id,))
        conn.execute("DELETE FROM case_notes WHERE case_id = ?", (case_id,))
        conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    _audit_log(user_id, "delete", "case", str(case_id), f"Deleted case {case['case_id']}")
    return True


def restore_case(case_id: int, user_id: int) -> dict | None:
    return update_case(case_id, user_id, {"is_archived": False})


# ── 6.4 Evidence Management ──

def add_evidence(case_id: int, user_id: int, evidence_type: str, file_name: str = "", file_path: str = "", description: str = "", source: str = "") -> dict | None:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return None
    evidence_type = evidence_type if evidence_type in VALID_EVIDENCE_TYPES else "other"
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO case_evidence (case_id, evidence_type, file_name, file_path, description, source) VALUES (?, ?, ?, ?, ?, ?)",
            (case_id, evidence_type, file_name, file_path, description, source),
        )
        row = conn.execute("SELECT * FROM case_evidence WHERE id = ?", (cur.lastrowid,)).fetchone()
    _log_activity(case_id, user_id, "evidence_added", f"Added {evidence_type}: {file_name or description}")
    _audit_log(user_id, "create", "evidence", str(case_id), f"Added {evidence_type} evidence to case {case['case_id']}")
    return dict(row)


def list_evidence(case_id: int, user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return []
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM case_evidence WHERE case_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (case_id, limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def remove_evidence(evidence_id: int, case_id: int, user_id: int) -> bool:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return False
    with get_db() as conn:
        row = conn.execute("SELECT * FROM case_evidence WHERE id = ? AND case_id = ?", (evidence_id, case_id)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM case_evidence WHERE id = ?", (evidence_id,))
    _log_activity(case_id, user_id, "evidence_removed", f"Removed evidence {evidence_id}")
    _audit_log(user_id, "delete", "evidence", str(case_id), f"Removed evidence {evidence_id} from case {case['case_id']}")
    return True


# ── 6.1 Incident Report Generator ──

def generate_report(case_id: int, user_id: int, req: dict) -> dict:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return None

    content = _render_report_content(case, req)
    executive_summary = req.get("executive_summary", "")
    technical_summary = req.get("technical_summary", "")
    attack_timeline = json.dumps(req.get("attack_timeline", []))
    ioc_list = json.dumps(req.get("ioc_list", []))
    mitre_mapping = json.dumps(req.get("mitre_mapping", []))

    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO case_reports (case_id, title, content, executive_summary, technical_summary,
               attack_timeline, ioc_list, mitre_mapping)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (case_id, req.get("title", "Incident Report"), content,
             executive_summary, technical_summary, attack_timeline, ioc_list, mitre_mapping),
        )
        row = conn.execute("SELECT * FROM case_reports WHERE id = ?", (cur.lastrowid,)).fetchone()
    _log_activity(case_id, user_id, "report_generated", f"Report: {req.get('title', 'Incident Report')}")
    _audit_log(user_id, "create", "report", case["case_id"], f"Generated report for case {case['case_id']}")
    return dict(row)


def list_reports(case_id: int, user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return []
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM case_reports WHERE case_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (case_id, limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


# ── 6.2 Report Export ──

def export_report(report_id: int, case_id: int, user_id: int, fmt: str = "markdown") -> dict | None:
    fmt = fmt.lower()
    if fmt not in VALID_REPORT_FORMATS:
        fmt = "markdown"

    case = _validate_case_access(case_id, user_id)
    if not case:
        return None

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM case_reports WHERE id = ? AND case_id = ?", (report_id, case_id)
        ).fetchone()
    if not row:
        return None
    report = dict(row)

    if fmt == "json":
        content = _export_json(report)
        filename = f"report_{report_id}.json"
        content_type = "application/json"
    elif fmt == "html":
        content = _export_html(report)
        filename = f"report_{report_id}.html"
        content_type = "text/html"
    elif fmt == "pdf":
        content = _export_html(report)
        filename = f"report_{report_id}.pdf"
        content_type = "application/pdf"
    else:
        content = report["content"]
        filename = f"report_{report_id}.md"
        content_type = "text/markdown"

    _audit_log(user_id, "export", "report", f"{case_id}:{report_id}", f"Exported report as {fmt}")
    return {
        "content": content,
        "format": fmt,
        "filename": filename,
        "content_type": content_type,
    }


def _export_json(report: dict) -> str:
    return json.dumps({
        "title": report["title"],
        "executive_summary": report["executive_summary"],
        "technical_summary": report["technical_summary"],
        "attack_timeline": json.loads(report["attack_timeline"] or "[]"),
        "ioc_list": json.loads(report["ioc_list"] or "[]"),
        "mitre_mapping": json.loads(report["mitre_mapping"] or "[]"),
        "content": report["content"],
        "created_at": report["created_at"],
    }, indent=2)


def _export_html(report: dict) -> str:
    md = report["content"]
    html = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = []
    in_list = False
    for line in html.split("\n"):
        if line.startswith("## "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("- "):
            if not in_list:
                lines.append("<ul>")
                in_list = True
            lines.append(f"<li>{line[2:]}</li>")
        elif line.strip() == "":
            if in_list:
                lines.append("</ul>")
                in_list = False
        else:
            if in_list:
                lines.append("</ul>")
                in_list = False
            lines.append(f"<p>{line}</p>")
    if in_list:
        lines.append("</ul>")
    body = "\n".join(lines)
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>{report['title']}</title>
<style>
body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }}
h2 {{ color: #1a237e; border-bottom: 2px solid #1a237e; padding-bottom: 5px; }}
h3 {{ color: #283593; }}
ul {{ margin-left: 20px; }}
@media print {{ body {{ margin: 0; padding: 20px; }} }}
</style></head>
<body>
<h1>{report['title']}</h1>
{body}
</body></html>"""


# ── 6.5 Investigation Timeline ──

def get_investigation_timeline(case_id: int, user_id: int) -> dict:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return None

    evidence_rows = []
    activity_rows = []
    with get_db() as conn:
        evidence_rows = conn.execute(
            "SELECT * FROM case_evidence WHERE case_id = ? ORDER BY created_at ASC", (case_id,)
        ).fetchall()
        activity_rows = conn.execute(
            "SELECT ca.*, u.username FROM case_activity ca JOIN users u ON ca.user_id = u.id WHERE ca.case_id = ? ORDER BY ca.created_at ASC",
            (case_id,),
        ).fetchall()

    events = []
    for e in evidence_rows:
        ed = dict(e)
        events.append({
            "timestamp": ed["created_at"],
            "type": "evidence",
            "description": f"Evidence added: {ed['evidence_type']} - {ed['file_name'] or ed['description']}",
            "severity": "info",
        })
    for a in activity_rows:
        ad = dict(a)
        sev = "high" if "critical" in ad["action"].lower() else "medium" if "update" in ad["action"].lower() else "info"
        events.append({
            "timestamp": ad["created_at"],
            "type": "activity",
            "description": f"{ad['username']}: {ad['action']} - {ad['details']}",
            "severity": sev,
        })

    events.sort(key=lambda x: x["timestamp"])
    critical = [e for e in events if e["severity"] == "high"]
    stages = _identify_attack_stages(events)

    ai_summary = ""
    if events:
        ai_summary = f"Analysis of {len(events)} events: "
        type_counts = {}
        for e in events:
            type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
        ai_summary += f"{type_counts.get('activity', 0)} activities, {type_counts.get('evidence', 0)} evidence items. "
        if critical:
            ai_summary += f"{len(critical)} critical events identified."
        else:
            ai_summary += "No critical events detected."

    return {
        "events": events,
        "critical_events": critical,
        "attack_stages": stages,
        "summary": ai_summary,
    }


def _identify_attack_stages(events: list[dict]) -> list[str]:
    stages = []
    descriptions = " ".join(e["description"].lower() for e in events)
    if any(kw in descriptions for kw in ("phishing", "malware", "suspicious file", "download")):
        stages.append("Initial Access")
    if any(kw in descriptions for kw in ("execution", "process", "powershell", "script")):
        stages.append("Execution")
    if any(kw in descriptions for kw in ("persistence", "service", "registry", "startup")):
        stages.append("Persistence")
    if any(kw in descriptions for kw in ("credential", "password", "login", "brute")):
        stages.append("Credential Access")
    if any(kw in descriptions for kw in ("lateral", "network", "connection", "remote")):
        stages.append("Lateral Movement")
    if any(kw in descriptions for kw in ("exfiltrat", "data", "upload")):
        stages.append("Exfiltration")
    if not stages:
        stages.append("Investigation Ongoing")
    return stages


# ── 6.7 Collaboration ──

def add_comment(case_id: int, user_id: int, content: str, is_internal: bool = False) -> dict | None:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return None
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO case_comments (case_id, user_id, content, is_internal) VALUES (?, ?, ?, ?)",
            (case_id, user_id, content, 1 if is_internal else 0),
        )
        row = conn.execute("SELECT cc.*, u.username FROM case_comments cc JOIN users u ON cc.user_id = u.id WHERE cc.id = ?", (cur.lastrowid,)).fetchone()
    label = "internal note" if is_internal else "comment"
    _log_activity(case_id, user_id, f"{label}_added", f"Added {label}: {content[:80]}")
    _audit_log(user_id, "create", f"case_{label}", str(case_id), f"Added {label} to case")
    return dict(row)


def list_comments(case_id: int, user_id: int, include_internal: bool = False) -> list[dict]:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return []
    with get_db() as conn:
        if include_internal:
            rows = conn.execute(
                "SELECT cc.*, u.username FROM case_comments cc JOIN users u ON cc.user_id = u.id WHERE cc.case_id = ? ORDER BY cc.created_at DESC",
                (case_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT cc.*, u.username FROM case_comments cc JOIN users u ON cc.user_id = u.id WHERE cc.case_id = ? AND cc.is_internal = 0 ORDER BY cc.created_at DESC",
                (case_id,),
            ).fetchall()
    return [dict(r) for r in rows]


# ── 6.6 Report Templates ──

def list_templates() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM report_templates ORDER BY category, name").fetchall()
    return [dict(r) for r in rows]


def get_template(template_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM report_templates WHERE id = ?", (template_id,)).fetchone()
    return dict(row) if row else None


def create_template(name: str, content: str, category: str = "custom", is_default: bool = False) -> dict:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO report_templates (name, category, content, is_default) VALUES (?, ?, ?, ?)",
            (name, category, content, 1 if is_default else 0),
        )
        row = conn.execute("SELECT * FROM report_templates WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def render_template(template_id: int, variables: dict) -> str | None:
    tmpl = get_template(template_id)
    if not tmpl:
        return None
    content = tmpl["content"]
    for var in TEMPLATE_VARIABLES:
        val = variables.get(var, "")
        if isinstance(val, list):
            val = "\n".join(f"- {v}" for v in val)
        elif isinstance(val, dict):
            val = json.dumps(val, indent=2)
        content = content.replace(f"{{{{{var}}}}}", str(val))
    return content


# ── 6.8 Search & Archive ──

def search_cases(user_id: int, params: dict) -> list[dict]:
    query = params.get("query", "")
    status = params.get("status", "")
    severity = params.get("severity", "")
    case_type = params.get("case_type", "")
    assigned_analyst = params.get("assigned_analyst", "")
    date_from = params.get("date_from", "")
    date_to = params.get("date_to", "")
    is_archived = params.get("is_archived")
    limit = min(int(params.get("limit", 50)), 200)
    offset = int(params.get("offset", 0))

    conditions = ["user_id = ?"]
    args = [user_id]

    if is_archived is not None:
        conditions.append("is_archived = ?")
        args.append(1 if is_archived else 0)
    if status:
        conditions.append("status = ?")
        args.append(status)
    if severity:
        conditions.append("severity = ?")
        args.append(severity)
    if case_type:
        conditions.append("case_type = ?")
        args.append(case_type)
    if assigned_analyst:
        conditions.append("assigned_analyst LIKE ?")
        args.append(f"%{assigned_analyst}%")
    if date_from:
        conditions.append("created_at >= ?")
        args.append(date_from)
    if date_to:
        conditions.append("created_at <= ?")
        args.append(date_to)
    if query:
        conditions.append("(title LIKE ? OR description LIKE ? OR case_id LIKE ? OR findings LIKE ?)")
        q = f"%{query}%"
        args.extend([q, q, q, q])

    with get_db() as conn:
        sql = f"""SELECT id, case_id, title, status, severity, case_type, assigned_analyst,
                         is_archived, created_at, updated_at
                  FROM cases WHERE {' AND '.join(conditions)}
                  ORDER BY updated_at DESC LIMIT ? OFFSET ?"""
        args.extend([limit, offset])
        rows = conn.execute(sql, args).fetchall()
    return [dict(r) for r in rows]


def list_archived_cases(user_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, case_id, title, status, severity, case_type, assigned_analyst,
                      is_archived, created_at, updated_at
               FROM cases WHERE user_id = ? AND is_archived = 1
               ORDER BY updated_at DESC""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── 6.9 Audit Trail ──

def get_audit_log(user_id: int = None, entity_type: str = "", entity_id: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    conditions = []
    args = []
    if user_id is not None:
        conditions.append("user_id = ?")
        args.append(user_id)
    if entity_type:
        conditions.append("entity_type = ?")
        args.append(entity_type)
    if entity_id:
        conditions.append("entity_id = ?")
        args.append(entity_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT al.*, u.username FROM audit_log al
                JOIN users u ON al.user_id = u.id
                {where} ORDER BY al.created_at DESC LIMIT ? OFFSET ?""",
            args + [min(limit, 500), offset],
        ).fetchall()
    return [dict(r) for r in rows]


def get_case_activity(case_id: int, user_id: int) -> list[dict] | None:
    case = _validate_case_access(case_id, user_id)
    if not case:
        return None
    with get_db() as conn:
        rows = conn.execute(
            """SELECT ca.*, u.username FROM case_activity ca
               JOIN users u ON ca.user_id = u.id
               WHERE ca.case_id = ? ORDER BY ca.created_at DESC""",
            (case_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Internal helpers ──

def _render_report_content(case: dict, req: dict) -> str:
    lines = [f"# {req.get('title', 'Incident Report')}"]
    lines.append("")
    if req.get("executive_summary"):
        lines.append("## Executive Summary")
        lines.append(req["executive_summary"])
        lines.append("")
    if req.get("technical_summary"):
        lines.append("## Technical Summary")
        lines.append(req["technical_summary"])
        lines.append("")
    if req.get("attack_timeline"):
        lines.append("## Attack Timeline")
        for entry in req["attack_timeline"]:
            lines.append(f"- **{entry.get('timestamp', '')}** - {entry.get('event', '')}")
        lines.append("")
    if req.get("ioc_list"):
        lines.append("## Indicators of Compromise")
        for ioc in req["ioc_list"]:
            lines.append(f"- **{ioc.get('type', '')}**: `{ioc.get('value', '')}` ({ioc.get('context', '')})")
        lines.append("")
    if req.get("mitre_mapping"):
        lines.append("## MITRE ATT&CK Mapping")
        for m in req["mitre_mapping"]:
            lines.append(f"- **{m.get('technique_id', '')}**: {m.get('technique_name', '')} ({m.get('tactic', '')})")
        lines.append("")
    if req.get("root_cause"):
        lines.append("## Root Cause Analysis")
        lines.append(req["root_cause"])
        lines.append("")
    if req.get("impact_assessment"):
        lines.append("## Impact Assessment")
        lines.append(req["impact_assessment"])
        lines.append("")
    if req.get("containment_steps"):
        lines.append("## Containment Recommendations")
        for step in req["containment_steps"]:
            lines.append(f"- {step}")
        lines.append("")
    if req.get("recovery_steps"):
        lines.append("## Recovery Recommendations")
        for step in req["recovery_steps"]:
            lines.append(f"- {step}")
        lines.append("")
    if req.get("lessons_learned"):
        lines.append("## Lessons Learned")
        lines.append(req["lessons_learned"])
        lines.append("")
    return "\n".join(lines).strip()
