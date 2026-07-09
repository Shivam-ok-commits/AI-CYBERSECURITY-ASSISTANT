from datetime import datetime

from pydantic import BaseModel


class CaseCreate(BaseModel):
    title: str
    description: str = ""
    case_type: str = "incident"
    severity: str = "medium"
    assigned_analyst: str = ""


class CaseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    severity: str | None = None
    case_type: str | None = None
    assigned_analyst: str | None = None
    findings: str | None = None
    root_cause: str | None = None
    impact_assessment: str | None = None
    containment_steps: str | None = None
    recovery_steps: str | None = None
    lessons_learned: str | None = None
    is_archived: bool | None = None


class CaseResponse(BaseModel):
    id: int
    case_id: str
    title: str
    description: str
    status: str
    severity: str
    case_type: str
    user_id: int
    assigned_analyst: str
    findings: str
    root_cause: str
    impact_assessment: str
    containment_steps: str
    recovery_steps: str
    lessons_learned: str
    is_archived: bool
    created_at: str
    updated_at: str
    closed_at: str | None = None


class CaseListResponse(BaseModel):
    id: int
    case_id: str
    title: str
    status: str
    severity: str
    case_type: str
    assigned_analyst: str
    is_archived: bool
    created_at: str
    updated_at: str


class EvidenceCreate(BaseModel):
    evidence_type: str
    file_name: str = ""
    file_path: str = ""
    description: str = ""
    source: str = ""


class EvidenceResponse(BaseModel):
    id: int
    case_id: int
    evidence_type: str
    file_name: str
    file_path: str
    description: str
    source: str
    created_at: str


class ReportGenerateRequest(BaseModel):
    title: str = "Incident Report"
    executive_summary: str = ""
    technical_summary: str = ""
    attack_timeline: list[dict] = []
    ioc_list: list[dict] = []
    mitre_mapping: list[dict] = []
    root_cause: str = ""
    impact_assessment: str = ""
    containment_steps: list[str] = []
    recovery_steps: list[str] = []
    lessons_learned: str = ""


class ReportResponse(BaseModel):
    id: int
    case_id: int
    title: str
    format: str
    content: str
    executive_summary: str
    technical_summary: str
    attack_timeline: str
    ioc_list: str
    mitre_mapping: str
    created_at: str
    updated_at: str


class CommentCreate(BaseModel):
    content: str
    is_internal: bool = False


class CommentResponse(BaseModel):
    id: int
    case_id: int
    user_id: int
    username: str = ""
    content: str
    is_internal: bool
    created_at: str


class ActivityResponse(BaseModel):
    id: int
    case_id: int
    user_id: int
    username: str = ""
    action: str
    details: str
    created_at: str


class CaseNoteCreate(BaseModel):
    content: str


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    username: str = ""
    action: str
    entity_type: str
    entity_id: str
    details: str
    ip_address: str
    created_at: str


class TemplateCreate(BaseModel):
    name: str
    category: str = "custom"
    content: str
    is_default: bool = False


class TemplateResponse(BaseModel):
    id: int
    name: str
    category: str
    content: str
    is_default: bool
    created_at: str


class CaseSearchParams(BaseModel):
    query: str = ""
    status: str = ""
    severity: str = ""
    case_type: str = ""
    assigned_analyst: str = ""
    date_from: str = ""
    date_to: str = ""
    is_archived: bool | None = None
    limit: int = 50
    offset: int = 0


class ReportExportResponse(BaseModel):
    content: str
    format: str
    filename: str
    content_type: str
