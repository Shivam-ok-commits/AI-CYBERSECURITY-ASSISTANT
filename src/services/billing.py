from typing import Optional

from src.database import get_db

PLANS = {
    "free": {"api_limit": 1000, "user_limit": 5, "storage_mb": 512, "price": 0},
    "starter": {"api_limit": 10000, "user_limit": 20, "storage_mb": 5120, "price": 49},
    "professional": {"api_limit": 100000, "user_limit": 100, "storage_mb": 51200, "price": 199},
    "enterprise": {"api_limit": 999999999, "user_limit": 9999, "storage_mb": 999999, "price": 999},
}


def get_subscription(org_id: int) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM subscriptions WHERE org_id = ?", (org_id,)).fetchone()
    return dict(row) if row else None


def change_plan(org_id: int, plan: str) -> bool:
    if plan not in PLANS:
        return False
    with get_db() as conn:
        cur = conn.execute("""
            UPDATE subscriptions SET plan = ?, api_limit = ?, user_limit = ?, storage_limit_mb = ?
            WHERE org_id = ?
        """, (plan, PLANS[plan]["api_limit"], PLANS[plan]["user_limit"], PLANS[plan]["storage_mb"], org_id))
        return cur.rowcount > 0


def check_api_limit(org_id: int) -> bool:
    with get_db() as conn:
        sub = conn.execute("SELECT api_limit FROM subscriptions WHERE org_id = ?", (org_id,)).fetchone()
        if not sub:
            return True
        count = conn.execute(
            "SELECT COUNT(*) as c FROM api_metrics WHERE timestamp > datetime('now', '-1 day') AND user_id IN (SELECT user_id FROM org_members WHERE org_id = ?)",
            (org_id,),
        ).fetchone()["c"]
        return count < sub["api_limit"]


def list_plans() -> dict:
    return PLANS
