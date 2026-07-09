from fastapi import APIRouter

from src.database import get_db
from src.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health():
    db_status = "ok"
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
    except Exception:
        db_status = "error"
    return HealthResponse(status="ok", version="0.1.0", database=db_status)
