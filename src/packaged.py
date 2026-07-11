"""Entry point for PyInstaller-packaged backend."""
import os
import sys
from pathlib import Path

_MEIPASS = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _MEIPASS)

# Ensure data directories exist before importing app
from src.config import settings
Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)

# Import app directly so PyInstaller traces all dependencies
from src.api import app  # noqa: E402

import uvicorn  # noqa: E402

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        workers=1,
        log_level=os.getenv("LOG_LEVEL", "info"),
    )
