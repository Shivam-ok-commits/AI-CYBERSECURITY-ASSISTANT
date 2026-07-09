import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRouter

from src.config import settings
from src.database import init_db
from src.middleware import RequestLoggingMiddleware, add_error_handlers
from src.routers import ai_router, auth_router, case_management_router, dashboard_router, detection_router, enterprise_router, health_router, logs_router, threat_intel_router
from src.services.security import SecurityHeadersMiddleware, APIMetricsMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_router)
v1_router.include_router(auth_router)
v1_router.include_router(logs_router)
v1_router.include_router(threat_intel_router)
v1_router.include_router(ai_router)
v1_router.include_router(case_management_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(detection_router)
v1_router.include_router(enterprise_router)

app.include_router(v1_router)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
if os.getenv("ENABLE_RATE_LIMIT", "").lower() == "true":
    from src.services.security import RateLimitMiddleware, APIMetricsMiddleware
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(APIMetricsMiddleware)
add_error_handlers(app)
