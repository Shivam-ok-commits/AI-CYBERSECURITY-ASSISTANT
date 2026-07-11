import logging
import os
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRouter

from src.config import settings
from src.database import get_db, init_db
from src.middleware import RequestLoggingMiddleware, add_error_handlers
from src.routers import ai_router, auth_router, case_management_router, dashboard_router, detection_router, enterprise_router, health_router, logs_router, plugins_router, threat_intel_router
from src.services.security import SecurityHeadersMiddleware, APIMetricsMiddleware
from src.services.plugins import get_registry, load_bundled_plugins

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _seed_default_user() -> None:
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", ("admin",)).fetchone()
        if not existing:
            hashed = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO users (username, email, hashed_password, role) VALUES (?, ?, ?, ?)",
                ("admin", "admin@sentinel.local", hashed, "admin"),
            )
            logger.info("Seeded default admin user (admin/admin)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _seed_default_user()
    _init_plugins()
    logger.info("Application initialized")
    yield


def _init_plugins() -> None:
    registry = get_registry()
    bundled = load_bundled_plugins()
    for plugin in bundled:
        existing = registry.get(plugin.manifest.id)
        if not existing:
            registry.register(plugin)
    registry.load_persisted_state()
    logger.info("Loaded %d bundled plugins", len(bundled))


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

# Allow Electron renderer (file:// origin) to call the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
v1_router.include_router(plugins_router)

app.include_router(v1_router)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
if os.getenv("ENABLE_RATE_LIMIT", "").lower() == "true":
    from src.services.security import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIMetricsMiddleware)
add_error_handlers(app)
