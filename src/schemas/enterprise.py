from pydantic import BaseModel


# ── Notifications ──

class NotificationConfigCreate(BaseModel):
    channel: str
    event: str
    config: dict = {}


class NotificationConfigResponse(BaseModel):
    id: int
    channel: str
    event: str
    config: str
    enabled: bool


class SendNotificationRequest(BaseModel):
    channel: str
    event: str
    data: dict = {}
    to: str = ""
    webhook_url: str = ""


# ── Multi-tenant ──

class OrgCreate(BaseModel):
    name: str
    slug: str = ""


class OrgResponse(BaseModel):
    id: int
    name: str
    slug: str
    owner_id: int
    max_users: int
    max_storage_mb: int
    settings: str
    created_at: str


class OrgMemberAdd(BaseModel):
    user_id: int
    role: str = "member"


# ── Billing ──

class PlanChange(BaseModel):
    plan: str


class SubscriptionResponse(BaseModel):
    id: int
    org_id: int
    plan: str
    status: str
    api_limit: int
    user_limit: int
    storage_limit_mb: int


# ── Integrations ──

class IntegrationCreate(BaseModel):
    provider: str
    config: dict = {}


class IntegrationResponse(BaseModel):
    id: int
    provider: str
    config: str
    enabled: bool
    last_sync: str = ""


class IntegrationEventSend(BaseModel):
    event: dict


# ── Backup ──

class BackupResponse(BaseModel):
    id: int
    path: str
    size_bytes: int
    type: str
    status: str
    created_at: str


# ── Monitoring ──

class MetricResponse(BaseModel):
    id: int
    endpoint: str
    method: str
    status_code: int
    duration_ms: int
    timestamp: str
