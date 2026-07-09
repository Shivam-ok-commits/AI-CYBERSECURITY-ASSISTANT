from typing import Optional

from src.database import get_db


def create_organization(name: str, owner_id: int, slug: str = "", settings: Optional[dict] = None) -> dict:
    if not slug:
        slug = name.lower().replace(" ", "-")[:50]
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO organizations (name, slug, owner_id, settings) VALUES (?, ?, ?, ?)",
            (name, slug, owner_id, json_str(settings or {})),
        )
        org_id = cur.lastrowid
        conn.execute("INSERT INTO org_members (org_id, user_id, role) VALUES (?, ?, ?)", (org_id, owner_id, "admin"))
        conn.execute("INSERT INTO subscriptions (org_id, plan) VALUES (?, ?)", (org_id, "free"))
        return dict(conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone())


def get_organization(org_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)).fetchone()
    return dict(row) if row else None


def list_organizations(user_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT o.* FROM organizations o
            JOIN org_members m ON o.id = m.org_id
            WHERE m.user_id = ?
        """, (user_id,)).fetchall()
    return [dict(r) for r in rows]


def add_org_member(org_id: int, user_id: int, role: str = "member") -> bool:
    with get_db() as conn:
        org = conn.execute("SELECT max_users FROM organizations WHERE id = ?", (org_id,)).fetchone()
        if not org:
            return False
        count = conn.execute("SELECT COUNT(*) as c FROM org_members WHERE org_id = ?", (org_id,)).fetchone()["c"]
        if count >= org["max_users"]:
            return False
        try:
            conn.execute("INSERT INTO org_members (org_id, user_id, role) VALUES (?, ?, ?)", (org_id, user_id, role))
            return True
        except Exception:
            return False


def remove_org_member(org_id: int, user_id: int) -> bool:
    with get_db() as conn:
        cur = conn.execute("DELETE FROM org_members WHERE org_id = ? AND user_id = ?", (org_id, user_id))
        return cur.rowcount > 0


def update_org_settings(org_id: int, settings: dict) -> bool:
    with get_db() as conn:
        cur = conn.execute("UPDATE organizations SET settings = ? WHERE id = ?", (json_str(settings), org_id))
        return cur.rowcount > 0


def json_str(obj: dict) -> str:
    import json
    return json.dumps(obj)
