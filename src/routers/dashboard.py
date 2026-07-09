from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.database import get_db
from src.schemas.dashboard import (
    AlertCreate,
    AlertResponse,
    AlertUpdate,
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    DashboardSummary,
    NotificationCreate,
    NotificationResponse,
    UserSettingsResponse,
    UserSettingsUpdate,
)
from src.services.auth import get_current_user
from src.services.dashboard import (
    create_alert,
    create_asset,
    create_notification,
    delete_asset,
    get_alert,
    get_alert_stats,
    get_asset,
    get_attack_timeline_data,
    get_cve_trend_data,
    get_event_type_chart,
    get_executive_summary,
    get_full_dashboard,
    get_investigation_stats,
    get_ioc_trend_data,
    get_log_stats,
    get_severity_chart_data,
    get_threat_distribution,
    get_threat_intel_stats,
    get_unread_count,
    get_user_settings,
    list_alerts,
    list_assets,
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    update_alert,
    update_asset,
    update_user_settings,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ── 7.1 Security Dashboard ──

@router.get("/executive")
def executive_summary():
    return get_executive_summary()


@router.get("/summary", response_model=DashboardSummary)
def full_dashboard(user: dict = Depends(get_current_user)):
    return get_full_dashboard(user["id"])


# ── 7.2 Alert Center ──

@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert_endpoint(body: AlertCreate, user: dict = Depends(get_current_user)):
    return create_alert(user["id"], body.model_dump())


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts_endpoint(
    status: str = Query(""),
    severity: str = Query(""),
    alert_type: str = Query(""),
    assigned_to: str = Query(""),
    query: str = Query(""),
    limit: int = Query(50),
    offset: int = Query(0),
):
    return list_alerts(status, severity, alert_type, assigned_to, query, limit, offset)


@router.get("/alerts/stats")
def alert_stats():
    return get_alert_stats()


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert_endpoint(alert_id: int):
    alert = get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert_endpoint(alert_id: int, body: AlertUpdate, user: dict = Depends(get_current_user)):
    result = update_alert(alert_id, user["id"], body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return result


# ── 7.5 Asset Dashboard ──

@router.post("/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset_endpoint(body: AssetCreate):
    return create_asset(body.model_dump())


@router.get("/assets", response_model=list[AssetResponse])
def list_assets_endpoint(
    asset_type: str = Query(""),
    criticality: str = Query(""),
    is_active: bool | None = Query(None),
    query: str = Query(""),
    limit: int = Query(100),
    offset: int = Query(0),
):
    return list_assets(asset_type, criticality, is_active, query, limit, offset)


@router.get("/assets/{asset_id}", response_model=AssetResponse)
def get_asset_endpoint(asset_id: int):
    asset = get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return asset


@router.put("/assets/{asset_id}", response_model=AssetResponse)
def update_asset_endpoint(asset_id: int, body: AssetUpdate):
    result = update_asset(asset_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return result


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset_endpoint(asset_id: int):
    if not delete_asset(asset_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")


# ── 7.3 Investigation Dashboard ──

@router.get("/investigations/stats")
def investigation_stats():
    return get_investigation_stats()


# ── 7.4 Threat Intelligence Dashboard ──

@router.get("/threat/stats")
def threat_intel_stats():
    return get_threat_intel_stats()


# ── 7.6 Log Monitoring ──

@router.get("/logs/stats")
def log_stats():
    return get_log_stats()


# ── 7.7 Visual Analytics ──

@router.get("/charts/severity")
def severity_chart():
    return get_severity_chart_data()


@router.get("/charts/attack-timeline")
def attack_timeline_chart(days: int = Query(7)):
    return get_attack_timeline_data(days)


@router.get("/charts/threat-distribution")
def threat_distribution():
    return get_threat_distribution()


@router.get("/charts/ioc-trend")
def ioc_trend(days: int = Query(30)):
    return get_ioc_trend_data(days)


@router.get("/charts/cve-trend")
def cve_trend(days: int = Query(30)):
    return get_cve_trend_data(days)


@router.get("/charts/event-types")
def event_type_chart():
    return get_event_type_chart()


# ── 7.9 Notifications ──

@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification_endpoint(body: NotificationCreate, user: dict = Depends(get_current_user)):
    return create_notification(user["id"], body.model_dump())


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications_endpoint(
    unread_only: bool = Query(False),
    notif_type: str = Query(""),
    limit: int = Query(50),
    offset: int = Query(0),
    user: dict = Depends(get_current_user),
):
    return list_notifications(user["id"], unread_only, notif_type, limit, offset)


@router.get("/notifications/unread-count")
def unread_count(user: dict = Depends(get_current_user)):
    return {"count": get_unread_count(user["id"])}


@router.post("/notifications/{notif_id}/read")
def mark_read(notif_id: int, user: dict = Depends(get_current_user)):
    if not mark_notification_read(notif_id, user["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"ok": True}


@router.post("/notifications/read-all")
def mark_all_read(user: dict = Depends(get_current_user)):
    count = mark_all_notifications_read(user["id"])
    return {"ok": True, "marked": count}


# ── 7.11 Settings ──

@router.get("/settings", response_model=UserSettingsResponse)
def get_settings(user: dict = Depends(get_current_user)):
    settings = get_user_settings(user["id"])
    return settings


@router.put("/settings", response_model=UserSettingsResponse)
def update_settings(body: UserSettingsUpdate, user: dict = Depends(get_current_user)):
    result = update_user_settings(user["id"], body.model_dump(exclude_none=True))
    return result


# ── 7.10 User Management ──

@router.get("/users/analysts")
def list_analysts(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, username, email, role, created_at FROM users ORDER BY username"
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/users/activity")
def user_activity(limit: int = Query(50), offset: int = Query(0), user: dict = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT al.*, u.username FROM audit_log al
               JOIN users u ON al.user_id = u.id
               ORDER BY al.created_at DESC LIMIT ? OFFSET ?""",
            (min(limit, 500), offset),
        ).fetchall()
    return [dict(r) for r in rows]
