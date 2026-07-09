from pydantic import BaseModel


class AlertCreate(BaseModel):
    title: str
    description: str = ""
    severity: str = "medium"
    status: str = "open"
    alert_type: str = "other"
    source: str = ""
    source_id: str = ""
    assigned_to: str = ""
    ioc_value: str = ""
    event_count: int = 0
    raw_data: str = "{}"


class AlertUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    alert_type: str | None = None
    assigned_to: str | None = None
    event_count: int | None = None


class AlertResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    status: str
    alert_type: str
    source: str
    source_id: str
    user_id: int
    assigned_to: str
    ioc_value: str
    event_count: int
    raw_data: str
    resolved_at: str | None = None
    created_at: str
    updated_at: str


class AssetCreate(BaseModel):
    hostname: str = ""
    ip_address: str = ""
    asset_type: str = "host"
    os: str = ""
    department: str = ""
    location: str = ""
    owner: str = ""
    risk_score: float = 0.0
    criticality: str = "medium"
    is_active: bool = True
    tags: str = "[]"
    last_seen: str = ""


class AssetUpdate(BaseModel):
    hostname: str | None = None
    ip_address: str | None = None
    asset_type: str | None = None
    os: str | None = None
    department: str | None = None
    location: str | None = None
    owner: str | None = None
    risk_score: float | None = None
    criticality: str | None = None
    is_active: bool | None = None
    tags: str | None = None
    last_seen: str | None = None


class AssetResponse(BaseModel):
    id: int
    hostname: str
    ip_address: str
    asset_type: str
    os: str
    department: str
    location: str
    owner: str
    risk_score: float
    criticality: str
    is_active: bool
    tags: str
    last_seen: str | None = None
    created_at: str
    updated_at: str


class NotificationCreate(BaseModel):
    title: str
    message: str = ""
    notification_type: str = "info"
    severity: str = "info"
    link: str = ""


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    severity: str
    is_read: bool
    link: str
    created_at: str


class UserSettingsUpdate(BaseModel):
    preferences: str | None = None
    notification_config: str | None = None
    dashboard_layout: str | None = None


class UserSettingsResponse(BaseModel):
    id: int
    user_id: int
    preferences: str
    notification_config: str
    dashboard_layout: str
    updated_at: str


class ExecutiveSummary(BaseModel):
    total_alerts: int
    critical_alerts: int
    open_cases: int
    active_investigations: int
    total_iocs: int
    total_assets: int
    high_risk_assets: int
    risk_score: float
    security_health: str


class AlertStats(BaseModel):
    total: int
    by_severity: dict
    by_status: dict
    by_type: dict
    recent: list[dict]


class InvestigationStats(BaseModel):
    total: int
    open: int
    closed: int
    in_progress: int
    by_severity: dict
    avg_resolution_time: str


class ThreatIntelStats(BaseModel):
    total_iocs: int
    by_type: dict
    top_threats: list[dict]
    recent_cves: list[str]
    recent_malware: list[str]


class ChartDataPoint(BaseModel):
    label: str
    value: float


class ChartData(BaseModel):
    labels: list[str]
    datasets: list[dict]


class LogStats(BaseModel):
    total_events: int
    by_severity: dict
    by_event_type: dict
    top_source_ips: list[dict]
    recent_activity: list[dict]


class DashboardSummary(BaseModel):
    executive: ExecutiveSummary
    alerts: AlertStats
    investigations: InvestigationStats
    threat_intel: ThreatIntelStats
    assets: list[AssetResponse]
    log_stats: LogStats
    notifications: list[NotificationResponse]
