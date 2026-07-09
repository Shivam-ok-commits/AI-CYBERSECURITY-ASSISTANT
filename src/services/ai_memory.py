from src.database import get_db


def create_session(user_id: int, title: str = "New Chat", context_type: str = "general", context_id: int | None = None) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO chat_sessions (user_id, title, context_type, context_id) VALUES (?, ?, ?, ?)",
            (user_id, title, context_type, context_id),
        )
        return cur.lastrowid


def list_sessions(user_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_session(session_id: int, user_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id)
        ).fetchone()
    return dict(row) if row else None


def save_message(session_id: int, role: str, content: str, user_id: int = 0) -> int:
    u = user_id if user_id else 0
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO chats (user_id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (u, str(session_id), role, content),
        )
        conn.execute("UPDATE chat_sessions SET updated_at = datetime('now') WHERE id = ?", (session_id,))
        return cur.lastrowid


def get_history(session_id: int, limit: int = 50) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM chats WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (str(session_id), limit),
        ).fetchall()
    return [dict(r) for r in rows]


def add_evidence(session_id: int, message_id: int | None, evidence_type: str, evidence_id: str, summary: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO evidence_links (session_id, message_id, evidence_type, evidence_id, evidence_summary) VALUES (?, ?, ?, ?, ?)",
            (session_id, message_id, evidence_type, evidence_id, summary),
        )


def get_evidence(session_id: int) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM evidence_links WHERE session_id = ? ORDER BY created_at DESC", (session_id,)
        ).fetchall()
    return [dict(r) for r in rows]
