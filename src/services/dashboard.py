import json
from datetime import datetime, timezone

from src.database import get_db

ALERT_SEVERITIES = ("low", "medium", "high", "critical")
ALERT_STATUSES = ("open", "acknowledged", "investigating", "resolved", "dismissed")
ALERT_TYPES = ("malware", "ioc", "brute_force", "phishing", "anomaly", "policy", "vulnerability", "threat_intel", "other")
ASSET_TYPES = ("host", "server", "endpoint", "network_device", "cloud", "application", "database", "other")
CRITICALITY_LEVELS = ("low", "medium", "high", "critical")
NOTIF_TYPES = ("alert", "ioc", "malware", "investigation", "threat_feed", "system", "info")


def _dict_or_none(row):
    return dict(row) if row else None


def _ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ── 7.2 Alert Center ──

def create_alert(user_id: int, data: dict) -> dict:
    sev = data["severity"] if data["severity"] in ALERT_SEVERITIES else "medium"
    st = data["status"] if data["status"] in ALERT_STATUSES else "open"
    at = data["alert_type"] if data["alert_type"] in ALERT_TYPES else "other"
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO alerts (title, description, severity, status, alert_type, source, source_id, user_id,
               assigned_to, ioc_value, event_count, raw_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data["title"], data.get("description", ""), sev, st, at,
             data.get("source", ""), data.get("source_id", ""), user_id,
             data.get("assigned_to", ""), data.get("ioc_value", ""),
             int(data.get("event_count", 0)), data.get("raw_data", "{}")),
        )
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def update_alert(alert_id: int, user_id: int, data: dict) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        if not row:
            return None
        fields = []
        vals = []
        for k in ("title", "description", "severity", "status", "alert_type", "assigned_to", "event_count"):
            if k in data and data[k] is not None:
                if k == "severity" and data[k] not in ALERT_SEVERITIES:
                    continue
                if k == "status":
                    if data[k] not in ALERT_STATUSES:
                        continue
                    if data[k] == "resolved":
                        fields.append("resolved_at = ?")
                        vals.append(_ts())
                fields.append(f"{k} = ?")
                vals.append(data[k])
        if not fields:
            return dict(row)
        fields.append("updated_at = ?")
        vals.append(_ts())
        vals.append(alert_id)
        conn.execute(f"UPDATE alerts SET {', '.join(fields)} WHERE id = ?", vals)
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    return dict(row)


def get_alert(alert_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    return dict(row) if row else None


def list_alerts(status: str = "", severity: str = "", alert_type: str = "",
                assigned_to: str = "", query: str = "", limit: int = 50, offset: int = 0) -> list[dict]:
    conditions = []
    args = []
    if status:
        conditions.append("status = ?")
        args.append(status)
    if severity:
        conditions.append("severity = ?")
        args.append(severity)
    if alert_type:
        conditions.append("alert_type = ?")
        args.append(alert_type)
    if assigned_to:
        conditions.append("assigned_to LIKE ?")
        args.append(f"%{assigned_to}%")
    if query:
        conditions.append("(title LIKE ? OR description LIKE ? OR ioc_value LIKE ?)")
        q = f"%{query}%"
        args.extend([q, q, q])
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM alerts {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            args + [min(limit, 200), offset],
        ).fetchall()
    return [dict(r) for r in rows]


def get_alert_stats() -> dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM alerts").fetchone()["c"]
        by_severity = dict(conn.execute(
            "SELECT severity, COUNT(*) as c FROM alerts GROUP BY severity"
        ).fetchall())
        by_status = dict(conn.execute(
            "SELECT status, COUNT(*) as c FROM alerts GROUP BY status"
        ).fetchall())
        by_type = dict(conn.execute(
            "SELECT alert_type, COUNT(*) as c FROM alerts GROUP BY alert_type"
        ).fetchall())
        recent = conn.execute(
            "SELECT id, title, severity, status, alert_type, created_at FROM alerts ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
    return {
        "total": total,
        "by_severity": dict(by_severity),
        "by_status": dict(by_status),
        "by_type": dict(by_type),
        "recent": [dict(r) for r in recent],
    }


# ── 7.5 Asset Dashboard ──

def create_asset(data: dict) -> dict:
    at = data.get("asset_type", "host") if data.get("asset_type") in ASSET_TYPES else "host"
    cr = data.get("criticality", "medium") if data.get("criticality") in CRITICALITY_LEVELS else "medium"
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO assets (hostname, ip_address, asset_type, os, department, location, owner,
               risk_score, criticality, is_active, tags, last_seen)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.get("hostname", ""), data.get("ip_address", ""), at, data.get("os", ""),
             data.get("department", ""), data.get("location", ""), data.get("owner", ""),
             float(data.get("risk_score", 0)), cr, 1 if data.get("is_active", True) else 0,
             data.get("tags", "[]"), data.get("last_seen", "")),
        )
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def update_asset(asset_id: int, data: dict) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            return None
        fields = []
        vals = []
        for k in ("hostname", "ip_address", "asset_type", "os", "department", "location", "owner",
                   "risk_score", "criticality", "is_active", "tags", "last_seen"):
            if k in data and data[k] is not None:
                if k == "asset_type" and data[k] not in ASSET_TYPES:
                    continue
                if k == "criticality" and data[k] not in CRITICALITY_LEVELS:
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
        vals.append(asset_id)
        conn.execute(f"UPDATE assets SET {', '.join(fields)} WHERE id = ?", vals)
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    return dict(row)


def get_asset(asset_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    return dict(row) if row else None


def list_assets(asset_type: str = "", criticality: str = "", is_active: bool | None = None,
                query: str = "", limit: int = 100, offset: int = 0) -> list[dict]:
    conditions = []
    args = []
    if asset_type:
        conditions.append("asset_type = ?")
        args.append(asset_type)
    if criticality:
        conditions.append("criticality = ?")
        args.append(criticality)
    if is_active is not None:
        conditions.append("is_active = ?")
        args.append(1 if is_active else 0)
    if query:
        conditions.append("(hostname LIKE ? OR ip_address LIKE ? OR owner LIKE ? OR department LIKE ?)")
        q = f"%{query}%"
        args.extend([q, q, q, q])
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM assets {where} ORDER BY risk_score DESC LIMIT ? OFFSET ?",
            args + [min(limit, 500), offset],
        ).fetchall()
    return [dict(r) for r in rows]


def delete_asset(asset_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT id FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    return True


# ── 7.9 Notifications ──

def create_notification(user_id: int, data: dict) -> dict:
    nt = data.get("notification_type", "info") if data.get("notification_type") in NOTIF_TYPES else "info"
    sev = data.get("severity", "info") if data.get("severity") in ALERT_SEVERITIES + ("info",) else "info"
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO notifications (user_id, title, message, notification_type, severity, link) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, data["title"], data.get("message", ""), nt, sev, data.get("link", "")),
        )
        row = conn.execute("SELECT * FROM notifications WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_notifications(user_id: int, unread_only: bool = False, notif_type: str = "",
                       limit: int = 50, offset: int = 0) -> list[dict]:
    conditions = ["user_id = ?"]
    args = [user_id]
    if unread_only:
        conditions.append("is_read = 0")
    if notif_type:
        conditions.append("notification_type = ?")
        args.append(notif_type)
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM notifications WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            args + [min(limit, 200), offset],
        ).fetchall()
    return [dict(r) for r in rows]


def mark_notification_read(notif_id: int, user_id: int) -> bool:
    with get_db() as conn:
        r = conn.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notif_id, user_id)
        )
        return r.rowcount > 0


def mark_all_notifications_read(user_id: int) -> int:
    with get_db() as conn:
        r = conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))
        return r.rowcount


def get_unread_count(user_id: int) -> int:
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,)).fetchone()
    return row["c"]


# ── 7.11 Settings ──

def get_user_settings(user_id: int) -> dict | None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,)
        )
        row = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_user_settings(user_id: int, data: dict) -> dict | None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,)
        )
        fields = []
        vals = []
        for k in ("preferences", "notification_config", "dashboard_layout"):
            if k in data and data[k] is not None:
                fields.append(f"{k} = ?")
                vals.append(data[k] if isinstance(data[k], str) else json.dumps(data[k]))
        if not fields:
            row = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
            return dict(row)
        fields.append("updated_at = ?")
        vals.append(_ts())
        vals.append(user_id)
        conn.execute(f"UPDATE user_settings SET {', '.join(fields)} WHERE user_id = ?", vals)
        row = conn.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row)


# ── 7.1 Executive / Security Dashboard ──

def get_executive_summary() -> dict:
    with get_db() as conn:
        total_alerts = conn.execute("SELECT COUNT(*) as c FROM alerts").fetchone()["c"]
        critical_alerts = conn.execute("SELECT COUNT(*) as c FROM alerts WHERE severity = 'critical' AND status != 'resolved' AND status != 'dismissed'").fetchone()["c"]
        open_cases = conn.execute("SELECT COUNT(*) as c FROM cases WHERE status IN ('open', 'in_progress') AND is_archived = 0").fetchone()["c"]
        total_iocs = conn.execute("SELECT COUNT(*) as c FROM ioc_reputation").fetchone()["c"]
        total_assets = conn.execute("SELECT COUNT(*) as c FROM assets").fetchone()["c"]
        high_risk = conn.execute("SELECT COUNT(*) as c FROM assets WHERE criticality IN ('high', 'critical') AND is_active = 1").fetchone()["c"]

    risk_score = _compute_risk_score(critical_alerts, open_cases, high_risk, total_assets)
    health = _compute_health(risk_score)
    return {
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "open_cases": open_cases,
        "active_investigations": open_cases,
        "total_iocs": total_iocs,
        "total_assets": total_assets,
        "high_risk_assets": high_risk,
        "risk_score": risk_score,
        "security_health": health,
    }


def _compute_risk_score(critical_alerts: int, open_cases: int, high_risk_assets: int, total_assets: int) -> float:
    score = 0.0
    score += min(critical_alerts * 15, 30)
    score += min(open_cases * 10, 25)
    if total_assets > 0:
        score += min((high_risk_assets / max(total_assets, 1)) * 25, 25)
    score += 20.0
    return round(min(max(score, 0), 100), 1)


def _compute_health(risk_score: float) -> str:
    if risk_score >= 80:
        return "critical"
    if risk_score >= 60:
        return "poor"
    if risk_score >= 40:
        return "fair"
    if risk_score >= 20:
        return "good"
    return "excellent"


# ── 7.3 Investigation Dashboard ──

def get_investigation_stats() -> dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM cases").fetchone()["c"]
        opened = conn.execute("SELECT COUNT(*) as c FROM cases WHERE status = 'open'").fetchone()["c"]
        closed = conn.execute("SELECT COUNT(*) as c FROM cases WHERE status = 'closed'").fetchone()["c"]
        in_progress = conn.execute("SELECT COUNT(*) as c FROM cases WHERE status = 'in_progress'").fetchone()["c"]
        by_sev = dict(conn.execute("SELECT severity, COUNT(*) as c FROM cases GROUP BY severity").fetchall())
        avg_row = conn.execute(
            "SELECT AVG(CAST(julianday(closed_at) - julianday(created_at) AS INTEGER)) as avg_days FROM cases WHERE closed_at IS NOT NULL"
        ).fetchone()
    avg_time = f"{round(avg_row['avg_days'], 1)} days" if avg_row and avg_row["avg_days"] else "N/A"
    return {
        "total": total,
        "open": opened,
        "closed": closed,
        "in_progress": in_progress,
        "by_severity": dict(by_sev),
        "avg_resolution_time": avg_time,
    }


# ── 7.4 Threat Intelligence Dashboard ──

def get_threat_intel_stats() -> dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM ioc_reputation").fetchone()["c"]
        by_type = dict(conn.execute("SELECT indicator_type, COUNT(*) as c FROM ioc_reputation GROUP BY indicator_type").fetchall())
        top = conn.execute(
            "SELECT indicator, indicator_type, threat_score FROM ioc_reputation ORDER BY threat_score DESC LIMIT 10"
        ).fetchall()
        cves = conn.execute(
            "SELECT indicator FROM ioc_reputation WHERE indicator_type = 'cve' ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        malware_hashes = conn.execute(
            "SELECT indicator FROM ioc_reputation WHERE indicator_type IN ('md5', 'sha1', 'sha256') AND threat_score >= 7 ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
    return {
        "total_iocs": total,
        "by_type": dict(by_type),
        "top_threats": [{"indicator": r["indicator"], "type": r["indicator_type"], "score": r["threat_score"]} for r in top],
        "recent_cves": [r["indicator"] for r in cves],
        "recent_malware": [r["indicator"] for r in malware_hashes],
    }


# ── 7.6 Log Monitoring ──

def get_log_stats(log_id: int | None = None) -> dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM parsed_events").fetchone()["c"]
        by_severity = dict(conn.execute("SELECT severity, COUNT(*) as c FROM parsed_events GROUP BY severity").fetchall())
        by_type = dict(conn.execute("SELECT event_type, COUNT(*) as c FROM parsed_events GROUP BY event_type ORDER BY c DESC").fetchall())
        top_ips = conn.execute(
            "SELECT source_ip, COUNT(*) as c FROM parsed_events WHERE source_ip IS NOT NULL AND source_ip != '' GROUP BY source_ip ORDER BY c DESC LIMIT 10"
        ).fetchall()
        recent = conn.execute(
            "SELECT id, timestamp, event_type, severity, source_ip, raw FROM parsed_events ORDER BY id DESC LIMIT 20"
        ).fetchall()
    return {
        "total_events": total,
        "by_severity": dict(by_severity),
        "by_event_type": dict(by_type),
        "top_source_ips": [{"ip": r["source_ip"], "count": r["c"]} for r in top_ips],
        "recent_activity": [dict(r) for r in recent],
    }


# ── 7.7 Visual Analytics Charts ──

def get_severity_chart_data() -> dict:
    with get_db() as conn:
        alerts = dict(conn.execute("SELECT severity, COUNT(*) as c FROM alerts GROUP BY severity").fetchall())
        events = dict(conn.execute("SELECT severity, COUNT(*) as c FROM parsed_events GROUP BY severity").fetchall())
    all_sev = ["low", "medium", "high", "critical"]
    return {
        "labels": all_sev,
        "datasets": [
            {"label": "Alerts", "data": [alerts.get(s, 0) for s in all_sev]},
            {"label": "Events", "data": [events.get(s, 0) for s in all_sev]},
        ],
    }


def get_attack_timeline_data(days: int = 7) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DATE(created_at) as day, COUNT(*) as count, severity
               FROM alerts WHERE created_at >= datetime('now', ?)
               GROUP BY day, severity ORDER BY day""",
            (f"-{days} days",),
        ).fetchall()
    return [dict(r) for r in rows]


def get_threat_distribution() -> dict:
    with get_db() as conn:
        by_type = dict(conn.execute("SELECT indicator_type, COUNT(*) as c FROM ioc_reputation GROUP BY indicator_type ORDER BY c DESC").fetchall())
    return {"labels": list(by_type.keys()), "values": list(by_type.values())}


def get_ioc_trend_data(days: int = 30) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DATE(created_at) as day, COUNT(*) as count
               FROM ioc_reputation WHERE created_at >= datetime('now', ?)
               GROUP BY day ORDER BY day""",
            (f"-{days} days",),
        ).fetchall()
    return [dict(r) for r in rows]


def get_cve_trend_data(days: int = 30) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DATE(created_at) as day, COUNT(*) as count
               FROM ioc_reputation WHERE indicator_type = 'cve' AND created_at >= datetime('now', ?)
               GROUP BY day ORDER BY day""",
            (f"-{days} days",),
        ).fetchall()
    return [dict(r) for r in rows]


def get_event_type_chart() -> dict:
    with get_db() as conn:
        rows = conn.execute("SELECT event_type, COUNT(*) as c FROM parsed_events GROUP BY event_type ORDER BY c DESC LIMIT 10").fetchall()
    return {"labels": [r["event_type"] for r in rows], "values": [r["c"] for r in rows]}


# ── 7.12 Performance / Dashboard Cache ──

def get_full_dashboard(user_id: int) -> dict:
    executive = get_executive_summary()
    alerts = get_alert_stats()
    investigations = get_investigation_stats()
    threat_intel = get_threat_intel_stats()
    assets_list = list_assets(limit=10)
    log_stats = get_log_stats()
    notifs = list_notifications(user_id, limit=10)
    return {
        "executive": executive,
        "alerts": alerts,
        "investigations": investigations,
        "threat_intel": threat_intel,
        "assets": assets_list,
        "log_stats": log_stats,
        "notifications": notifs,
    }
