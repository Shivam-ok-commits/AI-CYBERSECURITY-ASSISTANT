from fastapi import APIRouter, Depends, HTTPException, status

from src.database import get_db
from src.schemas.ai import (
    AIProviderInfo,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ExplainRequest,
    ExplainResponse,
    InvestigationRequest,
    InvestigationResponse,
    PromptTemplate,
    RecommendationResponse,
    TimelineAnalysisResponse,
)
from src.services.ai_chat import (
    analyze_timeline,
    chat_completion,
    generate_recommendations,
    investigate_log,
)
from src.services.ai_explainer import explain_general
from src.services.ai_memory import create_session, get_history, get_session, list_sessions, save_message
from src.services.ai_prompts import get_prompt, list_prompts
from src.services.ai_rag import index_log_content, search_documents
from src.services.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


# ── Providers ──

@router.get("/providers", response_model=list[AIProviderInfo])
def list_ai_providers():
    from src.services.ai_providers import list_providers
    return list_providers()


@router.get("/providers/active", response_model=AIProviderInfo)
def get_active_provider():
    from src.services.ai_providers import get_provider
    provider = get_provider()
    return {"name": provider.name, "available": provider.is_available(), "requires_api_key": provider.requires_api_key}


@router.post("/providers/switch")
def switch_provider(body: dict):
    name = body.get("provider", "")
    from src.services.ai_providers import get_provider, list_providers
    available = {p["name"] for p in list_providers()}
    if name not in available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {name}")
    provider = get_provider(name)
    return {"name": provider.name, "available": provider.is_available(), "requires_api_key": provider.requires_api_key}


# ── Sessions ──


def _get_log_events(log_id: int, user_id: int) -> list[dict]:
    with get_db() as conn:
        log = conn.execute("SELECT id FROM uploaded_logs WHERE id = ? AND user_id = ?", (log_id, user_id)).fetchone()
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
        rows = conn.execute(
            "SELECT * FROM parsed_events WHERE log_id = ? ORDER BY line_number", (log_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Sessions ──

@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
def create_chat_session(body: ChatSessionCreate, user: dict = Depends(get_current_user)):
    sid = create_session(user["id"], body.title, body.context_type, body.context_id)
    return get_session(sid, user["id"])


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_chat_sessions(user: dict = Depends(get_current_user)):
    return list_sessions(user["id"])


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
def get_chat_session(session_id: int, user: dict = Depends(get_current_user)):
    session = get_session(session_id, user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/history")
def get_chat_history(session_id: int, user: dict = Depends(get_current_user)):
    session = get_session(session_id, user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return get_history(session_id)


# ── 5.1 Chat ──

@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, user: dict = Depends(get_current_user)):
    session = get_session(body.session_id, user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = await chat_completion(body.session_id, body.message, user["id"])
    return ChatResponse(**result)


# ── 5.2 Explain ──

@router.post("/explain", response_model=ExplainResponse)
def explain(body: ExplainRequest):
    explanation = explain_general(body.text)
    if not explanation:
        explanation = "I don't have specific information about this topic. Try using the event lookup or CVE endpoints for more details."
    return ExplainResponse(explanation=explanation, confidence=0.7 if explanation else 0.1)


# ── 5.3 Log Investigation ──

@router.post("/investigate", response_model=InvestigationResponse)
async def investigate(body: InvestigationRequest, user: dict = Depends(get_current_user)):
    if body.log_id:
        events = _get_log_events(body.log_id, user["id"])
        if not events:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found in this log")
        index_log_content(body.log_id, events)
        result = await investigate_log(body.log_id, events)
    elif body.evidence:
        from src.services.ai_explainer import explain_general
        explanation = explain_general(body.evidence)
        result = {
            "summary": explanation or "No analysis available.",
            "suspicious_patterns": [],
            "critical_events": [],
            "attack_chain": [],
            "priorities": [],
            "recommendations": [],
            "confidence": 0.7 if explanation else 0.1,
        }
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide log_id or evidence")
    return InvestigationResponse(**result)


# ── 5.4 Recommendations ──

@router.post("/recommendations", response_model=RecommendationResponse)
async def recommendations(body: InvestigationRequest, user: dict = Depends(get_current_user)):
    if body.log_id:
        events = _get_log_events(body.log_id, user["id"])
        result = await generate_recommendations(events)
    else:
        result = {"next_steps": [], "containment": [], "recovery": [], "patching": [], "detection_improvements": []}
    return RecommendationResponse(**result)


# ── 5.6 Timeline Analysis ──

@router.post("/timeline", response_model=TimelineAnalysisResponse)
async def timeline_analysis(body: InvestigationRequest, user: dict = Depends(get_current_user)):
    events = _get_log_events(body.log_id, user["id"])
    result = await analyze_timeline(events)
    return TimelineAnalysisResponse(**result)


# ── 5.7 Interactive Q&A ──

@router.post("/ask", response_model=ChatResponse)
async def ask(body: ChatRequest, user: dict = Depends(get_current_user)):
    session = get_session(body.session_id, user["id"])
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    result = await chat_completion(body.session_id, body.message, user["id"])
    return ChatResponse(**result)


# ── 5.9 Prompts ──

@router.get("/prompts", response_model=list[PromptTemplate])
def list_ai_prompts():
    return list_prompts()


@router.get("/prompts/{name}", response_model=PromptTemplate)
def get_ai_prompt(name: str):
    content = get_prompt(name)
    return PromptTemplate(name=name, category="general", content=content)


# ── 5.10 RAG ──

@router.post("/rag/search")
def rag_search(query: str, source_type: str = ""):
    results = search_documents(query, source_type if source_type else None)
    return {"results": results, "total": len(results)}


@router.post("/rag/index/log/{log_id}")
def rag_index_log(log_id: int, user: dict = Depends(get_current_user)):
    events = _get_log_events(log_id, user["id"])
    if not events:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No events found")
    index_log_content(log_id, events)
    return {"indexed": True, "chunks": len(events)}
