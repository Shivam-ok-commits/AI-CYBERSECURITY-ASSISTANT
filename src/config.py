import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Use proper user data directory when packaged, project dir otherwise
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.environ.get(
        'SENTINEL_DATA_DIR',
        Path(os.environ.get('APPDATA', Path.home() / '.local' / 'share')) / 'Sentinel'
    ))
else:
    BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    lmstudio_base_url: str = os.getenv("LMSTUDIO_BASE_URL", "")
    lmstudio_model: str = os.getenv("LMSTUDIO_MODEL", "local-model")
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    app_name: str = "AI Cybersecurity Assistant"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    database_path: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "assistant.db"))
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    uploads_dir: str = os.getenv("UPLOADS_DIR", str(BASE_DIR / "data" / "uploads"))
    virustotal_api_key: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    abuseipdb_api_key: str = os.getenv("ABUSEIPDB_API_KEY", "")
    otx_api_key: str = os.getenv("OTX_API_KEY", "")
    nvd_api_key: str = os.getenv("NVD_API_KEY", "")


settings = Settings()
