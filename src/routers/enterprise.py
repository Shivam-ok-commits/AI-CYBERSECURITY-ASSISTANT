import json

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.database import get_db
from src.schemas.enterprise import (
    BackupResponse, IntegrationCreate, IntegrationEventSend, IntegrationResponse,
    NotificationConfigCreate, NotificationConfigResponse, OrgCreate, OrgMemberAdd,
    OrgResponse, PlanChange, SendNotificationRequest, SubscriptionResponse,
)
from src.services.auth import get_current_user, require_role
from src.services.backup import create_backup, list_backups, restore_backup
from src.services.billing import change_plan, check_api_limit, get_subscription, list_plans
from src.services.integrations import CloudConnector, EDRConnector, SIEMConnector
from src.services.multi_tenant import (
    add_org_member, create_organization, get_organization,
    list_organizations, remove_org_member, update_org_settings,
)
from src.services.notifications import send_notification

router = APIRouter(prefix="/enterprise", tags=["enterprise"])


# ── Notifications ──

@router.get("/notifications", response_model=list[NotificationConfigResponse])
def list_notifications(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM notifications WHERE user_id = ?", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@router.post("/notifications", response_model=NotificationConfigResponse, status_code=status.HTTP_201_CREATED)
def create_notification(body: NotificationConfigCreate, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO notifications (user_id, channel, event, config) VALUES (?, ?, ?, ?)",
            (user["id"], body.channel, body.event, json.dumps(body.config)),
        )
        row = conn.execute("SELECT * FROM notifications WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@router.delete("/notifications/{notif_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(notif_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conn.execute("DELETE FROM notifications WHERE id = ? AND user_id = ?", (notif_id, user["id"]))


@router.post("/notifications/send")
def send_now(body: SendNotificationRequest, user: dict = Depends(get_current_user)):
    results = send_notification(user["id"], body.event, body.data)
    return {"results": results}


# ── Multi-tenant ──

@router.post("/orgs", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
def create_org(body: OrgCreate, user: dict = Depends(get_current_user)):
    org = create_organization(body.name, user["id"], body.slug)
    return org


@router.get("/orgs", response_model=list[OrgResponse])
def list_orgs(user: dict = Depends(get_current_user)):
    return list_organizations(user["id"])


@router.get("/orgs/{org_id}", response_model=OrgResponse)
def get_org(org_id: int):
    org = get_organization(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.post("/orgs/{org_id}/members")
def add_member(org_id: int, body: OrgMemberAdd):
    if not add_org_member(org_id, body.user_id, body.role):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to add member")
    return {"success": True}


@router.delete("/orgs/{org_id}/members/{user_id}")
def remove_member(org_id: int, user_id: int):
    if not remove_org_member(org_id, user_id):
        raise HTTPException(status_code=404, detail="Member not found")
    return {"success": True}


# ── Billing ──

@router.get("/plans")
def plans():
    return list_plans()


@router.get("/subscriptions/{org_id}", response_model=SubscriptionResponse)
def subscription(org_id: int):
    sub = get_subscription(org_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    return sub


@router.post("/subscriptions/{org_id}/change")
def change_subscription_plan(org_id: int, body: PlanChange):
    if not change_plan(org_id, body.plan):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan")
    return {"plan": body.plan}


@router.get("/subscriptions/{org_id}/check-limit")
def check_limit(org_id: int):
    return {"within_limit": check_api_limit(org_id)}


# ── Integrations ──

@router.get("/integrations", response_model=list[IntegrationResponse])
def list_integrations(org_id: int = Query(0)):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM integrations WHERE org_id = ?", (org_id,)).fetchall()
    return [dict(r) for r in rows]


@router.post("/integrations", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
def create_integration(body: IntegrationCreate, org_id: int = Query(0)):
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO integrations (org_id, provider, config) VALUES (?, ?, ?)",
            (org_id, body.provider, json.dumps(body.config)),
        )
        row = conn.execute("SELECT * FROM integrations WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@router.delete("/integrations/{int_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_integration(int_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM integrations WHERE id = ?", (int_id,))


@router.post("/integrations/{int_id}/test")
def test_integration(int_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM integrations WHERE id = ?", (int_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")

    config = json.loads(row["config"]) if isinstance(row["config"], str) else row["config"]
    config["provider"] = row["provider"]

    if row["provider"] in ("splunk", "elastic", "sentinel", "qradar"):
        siem = SIEMConnector(config)
        ok = siem.send_event({"test": True, "message": "Connection test from Cybersec Assistant"})
    elif row["provider"] in ("defender", "crowdstrike", "sentinelone"):
        edr = EDRConnector(config)
        alerts = edr.get_alerts()
        ok = len(alerts) >= 0
    elif row["provider"] in ("aws", "azure", "gcp"):
        cloud = CloudConnector(config)
        instances = cloud.list_instances()
        ok = len(instances) >= 0
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")

    # Update last_sync
    with get_db() as conn:
        conn.execute("UPDATE integrations SET last_sync = datetime('now') WHERE id = ?", (int_id,))

    return {"success": ok, "provider": row["provider"]}


@router.post("/integrations/{int_id}/send")
def send_integration_event(int_id: int, body: IntegrationEventSend):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM integrations WHERE id = ?", (int_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Integration not found")

    config = json.loads(row["config"]) if isinstance(row["config"], str) else row["config"]
    config["provider"] = row["provider"]

    siem = SIEMConnector(config)
    ok = siem.send_event(body.event)
    return {"success": ok}


# ── Backup ──

@router.post("/backups", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_backup_endpoint(user: dict = Depends(get_current_user)):
    return create_backup("manual")


@router.get("/backups", response_model=list[BackupResponse])
def list_backups_endpoint(limit: int = Query(20), offset: int = Query(0)):
    return list_backups(limit, offset)


@router.post("/backups/{backup_id}/restore")
def restore_backup_endpoint(backup_id: int, user: dict = Depends(require_role("admin"))):
    result = restore_backup(backup_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ── Monitoring (API metrics) ──

@router.get("/metrics")
def get_metrics(endpoint: str = Query(""), limit: int = Query(100), offset: int = Query(0)):
    with get_db() as conn:
        if endpoint:
            rows = conn.execute(
                "SELECT * FROM api_metrics WHERE endpoint = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (endpoint, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM api_metrics ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
    return [dict(r) for r in rows]


@router.get("/metrics/stats")
def get_metric_stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM api_metrics").fetchone()["c"]
        avg_duration = conn.execute("SELECT AVG(duration_ms) as a FROM api_metrics").fetchone()["a"] or 0
        top = conn.execute("""
            SELECT endpoint, COUNT(*) as hits, AVG(duration_ms) as avg_dur
            FROM api_metrics GROUP BY endpoint ORDER BY hits DESC LIMIT 10
        """).fetchall()
    return {"total_requests": total, "avg_duration_ms": round(avg_duration, 2), "top_endpoints": [dict(r) for r in top]}
