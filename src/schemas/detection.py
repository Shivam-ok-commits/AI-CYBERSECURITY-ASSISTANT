from pydantic import BaseModel


class DetectionRuleCreate(BaseModel):
    name: str
    description: str = ""
    rule_type: str = "custom"
    rule_format: str = "custom"
    category: str = "general"
    content: str = ""
    severity: str = "medium"
    mitre_attack_id: str = ""


class DetectionRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    content: str | None = None
    severity: str | None = None
    mitre_attack_id: str | None = None
    enabled: bool | None = None


class DetectionRuleResponse(BaseModel):
    id: int
    name: str
    description: str
    rule_type: str
    rule_format: str
    category: str
    content: str
    severity: str
    mitre_attack_id: str
    enabled: bool
    hit_count: int
    false_positive_count: int
    user_id: int
    created_at: str
    updated_at: str


class SigmaRuleCreate(BaseModel):
    title: str
    description: str = ""
    author: str = ""
    rule_id: str = ""
    logsource_category: str = ""
    logsource_product: str = ""
    logsource_service: str = ""
    detection: str = "{}"
    fields: str = "[]"
    falsepositives: str = "[]"
    level: str = "medium"
    tags: str = "[]"
    status: str = "experimental"
    content: str = ""


class SigmaRuleResponse(BaseModel):
    id: int
    title: str
    description: str
    author: str
    rule_id: str
    logsource_category: str
    logsource_product: str
    logsource_service: str
    detection: str
    fields: str
    falsepositives: str
    level: str
    tags: str
    status: str
    content: str
    enabled: bool
    hit_count: int
    created_at: str
    updated_at: str


class YARARuleCreate(BaseModel):
    name: str
    description: str = ""
    author: str = ""
    rule_id: str = ""
    content: str
    tags: str = "[]"
    malware_family: str = ""
    reference: str = ""


class YARARuleResponse(BaseModel):
    id: int
    name: str
    description: str
    author: str
    rule_id: str
    content: str
    tags: str
    malware_family: str
    reference: str
    enabled: bool
    hit_count: int
    compiled: bool
    created_at: str
    updated_at: str


class SavedHuntCreate(BaseModel):
    name: str
    description: str = ""
    hunt_type: str = "log"
    query: str = ""
    filters: str = "{}"


class SavedHuntResponse(BaseModel):
    id: int
    name: str
    description: str
    hunt_type: str
    query: str
    filters: str
    user_id: int
    is_scheduled: bool
    last_run: str | None = None
    created_at: str
    updated_at: str


class ScheduledJobCreate(BaseModel):
    name: str
    job_type: str
    config: str = "{}"
    schedule_interval: str = "daily"


class ScheduledJobResponse(BaseModel):
    id: int
    name: str
    job_type: str
    config: str
    schedule_interval: str
    is_active: bool
    last_run: str | None = None
    next_run: str | None = None
    user_id: int
    created_at: str
    updated_at: str


class AlertAutomationCreate(BaseModel):
    name: str
    description: str = ""
    trigger_type: str
    conditions: str = "{}"
    actions: str = "[]"
    priority: int = 0


class AlertAutomationResponse(BaseModel):
    id: int
    name: str
    description: str
    trigger_type: str
    conditions: str
    actions: str
    is_active: bool
    priority: int
    hit_count: int
    created_at: str
    updated_at: str


class WorkflowPlaybookCreate(BaseModel):
    name: str
    description: str = ""
    category: str = "general"
    steps: str = "[]"


class WorkflowPlaybookResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    steps: str
    is_active: bool
    created_at: str
    updated_at: str


class HuntResultResponse(BaseModel):
    id: int
    hunt_id: int | None = None
    hunt_type: str
    match_type: str
    match_value: str
    source: str
    severity: str
    context: str
    user_id: int
    created_at: str


class RuleHitResponse(BaseModel):
    id: int
    rule_type: str
    rule_id: int
    event_source: str
    match_detail: str
    severity: str
    is_false_positive: bool
    user_id: int
    created_at: str


class HuntingReportCreate(BaseModel):
    title: str
    hunt_type: str = "log"
    summary: str = ""
    findings: str = "[]"
    ioc_list: str = "[]"
    rule_matches: str = "[]"
    statistics: str = "{}"


class HuntingReportResponse(BaseModel):
    id: int
    title: str
    hunt_type: str
    summary: str
    findings: str
    ioc_list: str
    rule_matches: str
    statistics: str
    user_id: int
    created_at: str


class RuleTestResult(BaseModel):
    rule_id: int
    matched: bool
    matches: list[dict] = []
    execution_time_ms: float = 0.0
    error: str = ""


class AnalyticsResponse(BaseModel):
    total_rules: int
    enabled_rules: int
    total_hits: int
    false_positives: int
    false_positive_rate: float
    by_category: dict
    by_severity: dict
    by_mitre: dict
    top_rules: list[dict]
    hunting_metrics: dict
