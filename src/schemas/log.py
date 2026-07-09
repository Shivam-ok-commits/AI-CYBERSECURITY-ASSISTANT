from pydantic import BaseModel


class UploadLogResponse(BaseModel):
    id: int
    filename: str
    size_bytes: int
    source_type: str
    status: str
    event_count: int


class LogEntry(BaseModel):
    line_number: int
    timestamp: str | None = None
    source_ip: str | None = None
    event_type: str | None = None
    severity: str | None = None
    raw: str


class LogDetail(BaseModel):
    id: int
    filename: str
    source_type: str
    status: str
    size_bytes: int
    event_count: int
    created_at: str


class ExtractedEvent(BaseModel):
    event_name: str
    event_label: str
    line_number: int
    timestamp: str | None = None
    source_ip: str | None = None
    severity: str = "info"
    raw: str = ""


class SuspiciousFinding(BaseModel):
    type: str
    label: str
    source_ip: str | None = None
    severity: str = "medium"
    details: str = ""
    line_number: int | None = None


class TimelineBlock(BaseModel):
    timestamp: str
    event_count: int
    critical_count: int
    is_critical: bool
    entries: list[ExtractedEvent]


class StatsResponse(BaseModel):
    total_events: int
    suspicious_events: int
    failed_logins: int
    severity_distribution: dict[str, int]
    top_ips: list[dict]
    event_type_distribution: dict[str, int]
