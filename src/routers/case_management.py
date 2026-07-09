from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from src.database import get_db
from src.schemas.case_management import (
    ActivityResponse,
    AuditLogResponse,
    CaseCreate,
    CaseListResponse,
    CaseNoteCreate,
    CaseResponse,
    CaseUpdate,
    CommentCreate,
    CommentResponse,
    EvidenceCreate,
    EvidenceResponse,
    ReportGenerateRequest,
    ReportResponse,
    TemplateCreate,
    TemplateResponse,
)
from src.services.auth import get_current_user
from src.services.case_management import (
    add_comment,
    add_evidence,
    archive_case,
    create_case,
    create_template,
    delete_case,
    export_report,
    generate_report,
    get_case,
    get_case_activity,
    get_audit_log,
    get_investigation_timeline,
    get_template,
    list_cases,
    list_comments,
    list_evidence,
    list_reports,
    list_templates,
    remove_evidence,
    render_template,
    restore_case,
    search_cases,
    update_case,
)

router = APIRouter(prefix="/cases", tags=["case-management"])


# ── Static routes first (before parameterized routes) ──

# 6.6 Templates
@router.get("/templates", response_model=list[TemplateResponse])
def list_templates_endpoint():
    return list_templates()


@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template_endpoint(template_id: int):
    tmpl = get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return tmpl


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template_endpoint(body: TemplateCreate, user: dict = Depends(get_current_user)):
    return create_template(body.name, body.content, body.category, body.is_default)


@router.post("/templates/{template_id}/render")
def render_template_endpoint(template_id: int, variables: dict):
    result = render_template(template_id, variables)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return {"content": result}


# 6.8 Search
@router.get("/search/find", response_model=list[CaseListResponse])
def search_cases_endpoint(
    query: str = Query(""),
    status: str = Query(""),
    severity: str = Query(""),
    case_type: str = Query(""),
    assigned_analyst: str = Query(""),
    date_from: str = Query(""),
    date_to: str = Query(""),
    is_archived: bool | None = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    user: dict = Depends(get_current_user),
):
    params = {
        "query": query, "status": status, "severity": severity, "case_type": case_type,
        "assigned_analyst": assigned_analyst, "date_from": date_from, "date_to": date_to,
        "is_archived": is_archived, "limit": limit, "offset": offset,
    }
    return search_cases(user["id"], params)


# 6.8 Archived
@router.get("/archived/list", response_model=list[CaseListResponse])
def archived_cases_endpoint(user: dict = Depends(get_current_user)):
    return list_cases(user["id"], is_archived=True)


# 6.9 Audit
@router.get("/audit/logs", response_model=list[AuditLogResponse])
def get_audit_logs_endpoint(
    entity_type: str = Query(""),
    entity_id: str = Query(""),
    limit: int = Query(100),
    offset: int = Query(0),
    user: dict = Depends(get_current_user),
):
    return get_audit_log(entity_type=entity_type, entity_id=entity_id, limit=limit, offset=offset)


# ── Parameterized routes (must contain {case_id}) ──

@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case_endpoint(body: CaseCreate, user: dict = Depends(get_current_user)):
    return create_case(body.title, user["id"], body.description, body.case_type, body.severity, body.assigned_analyst)


@router.get("", response_model=list[CaseListResponse])
def list_cases_endpoint(archived: bool = Query(False), user: dict = Depends(get_current_user)):
    return list_cases(user["id"], archived)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    case = get_case(case_id, user["id"])
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


@router.put("/{case_id}", response_model=CaseResponse)
def update_case_endpoint(case_id: int, body: CaseUpdate, user: dict = Depends(get_current_user)):
    result = update_case(case_id, user["id"], body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    if not delete_case(case_id, user["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{case_id}/archive", response_model=CaseResponse)
def archive_case_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    result = archive_case(case_id, user["id"])
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result


@router.post("/{case_id}/restore", response_model=CaseResponse)
def restore_case_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    result = restore_case(case_id, user["id"])
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result


@router.post("/{case_id}/notes", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_note_endpoint(case_id: int, body: CaseNoteCreate, user: dict = Depends(get_current_user)):
    result = add_comment(case_id, user["id"], body.content, is_internal=True)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result


@router.get("/{case_id}/notes", response_model=list[CommentResponse])
def list_notes_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    return list_comments(case_id, user["id"], include_internal=True)


@router.post("/{case_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def add_evidence_endpoint(case_id: int, body: EvidenceCreate, user: dict = Depends(get_current_user)):
    result = add_evidence(case_id, user["id"], body.evidence_type, body.file_name, body.file_path, body.description, body.source)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result


@router.get("/{case_id}/evidence", response_model=list[EvidenceResponse])
def list_evidence_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    return list_evidence(case_id, user["id"])


@router.delete("/{case_id}/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_evidence_endpoint(case_id: int, evidence_id: int, user: dict = Depends(get_current_user)):
    if not remove_evidence(evidence_id, case_id, user["id"]):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")


@router.post("/{case_id}/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_report_endpoint(case_id: int, body: ReportGenerateRequest, user: dict = Depends(get_current_user)):
    result = generate_report(case_id, user["id"], body.model_dump())
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result


@router.get("/{case_id}/reports", response_model=list[ReportResponse])
def list_reports_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    return list_reports(case_id, user["id"])


@router.get("/{case_id}/reports/{report_id}/export")
def export_report_endpoint(case_id: int, report_id: int, fmt: str = Query("markdown"), user: dict = Depends(get_current_user)):
    result = export_report(report_id, case_id, user["id"], fmt)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return Response(content=result["content"], media_type=result["content_type"], headers={"Content-Disposition": f'attachment; filename="{result["filename"]}"'})


@router.get("/{case_id}/timeline")
def get_timeline_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    result = get_investigation_timeline(case_id, user["id"])
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result


@router.post("/{case_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def add_comment_endpoint(case_id: int, body: CommentCreate, user: dict = Depends(get_current_user)):
    result = add_comment(case_id, user["id"], body.content, body.is_internal)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result


@router.get("/{case_id}/comments", response_model=list[CommentResponse])
def list_comments_endpoint(case_id: int, internal: bool = Query(False), user: dict = Depends(get_current_user)):
    return list_comments(case_id, user["id"], include_internal=internal)


@router.get("/{case_id}/activity", response_model=list[ActivityResponse])
def get_activity_endpoint(case_id: int, user: dict = Depends(get_current_user)):
    result = get_case_activity(case_id, user["id"])
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return result
