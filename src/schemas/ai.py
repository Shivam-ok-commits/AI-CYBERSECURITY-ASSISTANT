from pydantic import BaseModel


class ChatSessionCreate(BaseModel):
    title: str = "New Chat"
    context_type: str = "general"
    context_id: int | None = None


class ChatSessionResponse(BaseModel):
    id: int
    title: str
    context_type: str
    context_id: int | None = None
    created_at: str
    updated_at: str


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: str | None = None


class ChatRequest(BaseModel):
    session_id: int
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    session_id: int
    reply: str
    evidence: list[dict] = []
    suggested_questions: list[str] = []
    confidence: float = 1.0


class ExplainRequest(BaseModel):
    text: str
    context_type: str = "general"


class ExplainResponse(BaseModel):
    explanation: str
    confidence: float
    sources: list[str] = []


class InvestigationRequest(BaseModel):
    log_id: int | None = None
    evidence: str = ""


class InvestigationResponse(BaseModel):
    summary: str
    suspicious_patterns: list[dict] = []
    critical_events: list[dict] = []
    attack_chain: list[str] = []
    priorities: list[dict] = []
    recommendations: list[str] = []
    confidence: float = 1.0


class RecommendationResponse(BaseModel):
    next_steps: list[str] = []
    containment: list[str] = []
    recovery: list[str] = []
    patching: list[str] = []
    detection_improvements: list[str] = []


class AIProviderInfo(BaseModel):
    name: str
    available: bool
    requires_api_key: bool


class TimelineAnalysisResponse(BaseModel):
    timeline: list[dict] = []
    attack_stages: list[str] = []
    root_cause: str = ""
    confidence: float = 1.0


class PromptTemplate(BaseModel):
    id: int | None = None
    name: str
    category: str
    content: str
    version: str = "1.0"
    is_active: bool = True
