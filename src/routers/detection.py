from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.schemas.detection import (
    AlertAutomationCreate,
    AlertAutomationResponse,
    AnalyticsResponse,
    DetectionRuleCreate,
    DetectionRuleResponse,
    DetectionRuleUpdate,
    HuntingReportCreate,
    HuntingReportResponse,
    HuntResultResponse,
    RuleTestResult,
    SavedHuntCreate,
    SavedHuntResponse,
    ScheduledJobCreate,
    ScheduledJobResponse,
    SigmaRuleCreate,
    SigmaRuleResponse,
    WorkflowPlaybookCreate,
    WorkflowPlaybookResponse,
    YARARuleCreate,
    YARARuleResponse,
)
from src.services.auth import get_current_user
from src.services.detection_engine import (
    create_alert_automation,
    create_detection_rule,
    create_hunting_report,
    create_saved_hunt,
    create_scheduled_job,
    create_sigma_rule,
    create_workflow_playbook,
    create_yara_rule,
    delete_alert_automation,
    delete_detection_rule,
    delete_saved_hunt,
    delete_scheduled_job,
    delete_sigma_rule,
    delete_workflow_playbook,
    delete_yara_rule,
    execute_hunt,
    execute_sigma_rule,
    export_sigma_rule,
    explain_rule,
    generate_sigma_from_natural,
    generate_yara_from_description,
    get_detection_analytics,
    get_detection_rule,
    get_saved_hunt,
    get_sigma_rule,
    get_workflow_playbook,
    get_yara_rule,
    improve_rule,
    list_alert_automations,
    list_detection_rules,
    list_hunting_reports,
    list_hunt_results,
    list_saved_hunts,
    list_scheduled_jobs,
    list_sigma_rules,
    list_workflow_playbooks,
    list_yara_rules,
    run_scheduled_job,
    scan_with_yara,
    test_detection_rule,
    update_alert_automation,
    update_detection_rule,
    update_scheduled_job,
    validate_sigma_rule,
    validate_yara_rule,
)

router = APIRouter(prefix="/detection", tags=["detection"])


# ── 8.1 Custom Detection Rules ──

@router.post("/rules", response_model=DetectionRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(body: DetectionRuleCreate, user: dict = Depends(get_current_user)):
    return create_detection_rule(user["id"], body.model_dump())


@router.get("/rules", response_model=list[DetectionRuleResponse])
def list_rules(
    category: str = Query(""), rule_type: str = Query(""), severity: str = Query(""),
    enabled_only: bool = Query(False), query: str = Query(""),
    limit: int = Query(100), offset: int = Query(0),
):
    return list_detection_rules(category, rule_type, severity, enabled_only, query, limit, offset)


@router.get("/rules/{rule_id}", response_model=DetectionRuleResponse)
def get_rule(rule_id: int):
    rule = get_detection_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return rule


@router.put("/rules/{rule_id}", response_model=DetectionRuleResponse)
def update_rule(rule_id: int, body: DetectionRuleUpdate, user: dict = Depends(get_current_user)):
    result = update_detection_rule(rule_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return result


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int):
    if not delete_detection_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")


@router.post("/rules/{rule_id}/test", response_model=RuleTestResult)
def test_rule(rule_id: int, sample_data: list[str]):
    return test_detection_rule(rule_id, sample_data)


# ── 8.2 Sigma Rules ──

@router.post("/sigma", response_model=SigmaRuleResponse, status_code=status.HTTP_201_CREATED)
def create_sigma(body: SigmaRuleCreate):
    return create_sigma_rule(body.model_dump())


@router.get("/sigma", response_model=list[SigmaRuleResponse])
def list_sigma(level: str = Query(""), status: str = Query(""), query: str = Query(""), limit: int = Query(100), offset: int = Query(0)):
    return list_sigma_rules(level, status, query, limit, offset)


@router.get("/sigma/{rule_id}", response_model=SigmaRuleResponse)
def get_sigma(rule_id: int):
    rule = get_sigma_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sigma rule not found")
    return rule


@router.delete("/sigma/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sigma(rule_id: int):
    if not delete_sigma_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sigma rule not found")


@router.post("/sigma/validate")
def validate_sigma(content: str):
    return validate_sigma_rule(content)


@router.post("/sigma/{rule_id}/execute")
def execute_sigma(rule_id: int, events: list[dict]):
    return execute_sigma_rule(rule_id, events)


@router.get("/sigma/{rule_id}/export")
def export_sigma(rule_id: int):
    result = export_sigma_rule(rule_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sigma rule not found")
    return result


# ── 8.3 YARA Rules ──

@router.post("/yara", response_model=YARARuleResponse, status_code=status.HTTP_201_CREATED)
def create_yara(body: YARARuleCreate):
    return create_yara_rule(body.model_dump())


@router.get("/yara", response_model=list[YARARuleResponse])
def list_yara(query: str = Query(""), enabled_only: bool = Query(False), limit: int = Query(100), offset: int = Query(0)):
    return list_yara_rules(query, enabled_only, limit, offset)


@router.get("/yara/{rule_id}", response_model=YARARuleResponse)
def get_yara(rule_id: int):
    rule = get_yara_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="YARA rule not found")
    return rule


@router.delete("/yara/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_yara(rule_id: int):
    if not delete_yara_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="YARA rule not found")


@router.post("/yara/validate")
def validate_yara(content: str):
    return validate_yara_rule(content)


@router.post("/yara/{rule_id}/scan")
def scan_yara(rule_id: int, file_contents: list[str]):
    return scan_with_yara(rule_id, file_contents)


# ── 8.4 Threat Hunting ──

# Static routes first
@router.get("/hunts/results", response_model=list[HuntResultResponse])
def list_hunt_results_endpoint(hunt_type: str = Query(""), limit: int = Query(100), offset: int = Query(0), user: dict = Depends(get_current_user)):
    return list_hunt_results(user["id"], hunt_type, limit, offset)


@router.post("/hunts", response_model=SavedHuntResponse, status_code=status.HTTP_201_CREATED)
def create_hunt(body: SavedHuntCreate, user: dict = Depends(get_current_user)):
    return create_saved_hunt(user["id"], body.model_dump())


@router.get("/hunts", response_model=list[SavedHuntResponse])
def list_hunts(hunt_type: str = Query(""), query: str = Query(""), limit: int = Query(100), offset: int = Query(0), user: dict = Depends(get_current_user)):
    return list_saved_hunts(user["id"], hunt_type, query, limit, offset)


@router.get("/hunts/{hunt_id}", response_model=SavedHuntResponse)
def get_hunt(hunt_id: int, user: dict = Depends(get_current_user)):
    hunt = get_saved_hunt(hunt_id, user["id"])
    if not hunt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hunt not found")
    return hunt


@router.delete("/hunts/{hunt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hunt(hunt_id: int, user: dict = Depends(get_current_user)):
    if not delete_saved_hunt(hunt_id, user["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hunt not found")


@router.post("/hunts/{hunt_id}/execute")
def execute_hunt_endpoint(hunt_id: int, user: dict = Depends(get_current_user)):
    result = execute_hunt(hunt_id, user["id"])
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    return result


# ── 8.5 Scheduled Scans ──

@router.post("/jobs", response_model=ScheduledJobResponse, status_code=status.HTTP_201_CREATED)
def create_job(body: ScheduledJobCreate, user: dict = Depends(get_current_user)):
    return create_scheduled_job(user["id"], body.model_dump())


@router.get("/jobs", response_model=list[ScheduledJobResponse])
def list_jobs(job_type: str = Query(""), active_only: bool = Query(False), limit: int = Query(100), offset: int = Query(0), user: dict = Depends(get_current_user)):
    return list_scheduled_jobs(user["id"], job_type, active_only, limit, offset)


@router.put("/jobs/{job_id}", response_model=ScheduledJobResponse)
def update_job(job_id: int, body: dict, user: dict = Depends(get_current_user)):
    result = update_scheduled_job(job_id, body)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return result


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int):
    if not delete_scheduled_job(job_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.post("/jobs/{job_id}/run")
def run_job(job_id: int):
    return run_scheduled_job(job_id)


# ── 8.6 Alert Automation ──

@router.post("/automation", response_model=AlertAutomationResponse, status_code=status.HTTP_201_CREATED)
def create_automation(body: AlertAutomationCreate):
    return create_alert_automation(body.model_dump())


@router.get("/automation", response_model=list[AlertAutomationResponse])
def list_automation(trigger_type: str = Query(""), active_only: bool = Query(False), limit: int = Query(100), offset: int = Query(0)):
    return list_alert_automations(trigger_type, active_only, limit, offset)


@router.put("/automation/{rule_id}", response_model=AlertAutomationResponse)
def update_automation(rule_id: int, body: dict):
    result = update_alert_automation(rule_id, body)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation rule not found")
    return result


@router.delete("/automation/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_automation(rule_id: int):
    if not delete_alert_automation(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation rule not found")


# ── 8.7 AI Rule Generator ──

@router.post("/ai/generate-sigma")
def ai_generate_sigma(text: str):
    return {"content": generate_sigma_from_natural(text)}


@router.post("/ai/generate-yara")
def ai_generate_yara(text: str):
    return {"content": generate_yara_from_description(text)}


@router.post("/ai/explain")
def ai_explain(content: str):
    return {"explanation": explain_rule(content)}


@router.post("/ai/improve")
def ai_improve(content: str, suggestion: str = ""):
    return {"content": improve_rule(content, suggestion)}


# ── 8.8 Workflow Automation ──

@router.post("/playbooks", response_model=WorkflowPlaybookResponse, status_code=status.HTTP_201_CREATED)
def create_playbook(body: WorkflowPlaybookCreate):
    return create_workflow_playbook(body.model_dump())


@router.get("/playbooks", response_model=list[WorkflowPlaybookResponse])
def list_playbooks(category: str = Query(""), active_only: bool = Query(False), limit: int = Query(100), offset: int = Query(0)):
    return list_workflow_playbooks(category, active_only, limit, offset)


@router.get("/playbooks/{playbook_id}", response_model=WorkflowPlaybookResponse)
def get_playbook(playbook_id: int):
    pb = get_workflow_playbook(playbook_id)
    if not pb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")
    return pb


@router.delete("/playbooks/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_playbook(playbook_id: int):
    if not delete_workflow_playbook(playbook_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playbook not found")


# ── 8.9 Hunting Reports ──

@router.post("/reports", response_model=HuntingReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(body: HuntingReportCreate, user: dict = Depends(get_current_user)):
    return create_hunting_report(user["id"], body.model_dump())


@router.get("/reports", response_model=list[HuntingReportResponse])
def list_reports(hunt_type: str = Query(""), limit: int = Query(100), offset: int = Query(0), user: dict = Depends(get_current_user)):
    return list_hunting_reports(user["id"], hunt_type, limit, offset)


# ── 8.10 Analytics ──

@router.get("/analytics", response_model=AnalyticsResponse)
def analytics():
    return get_detection_analytics()


@router.post("/analytics/hit")
def record_hit(rule_type: str, rule_id: int, event_source: str = "", match_detail: str = "", severity: str = "medium", user: dict = Depends(get_current_user)):
    from src.services.detection_engine import record_rule_hit
    record_rule_hit(rule_type, rule_id, event_source, match_detail, severity, user["id"])
    return {"ok": True}
