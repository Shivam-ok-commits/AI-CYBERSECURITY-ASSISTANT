import os
import shutil
import json
from datetime import datetime
from pathlib import Path

from src.config import settings
from src.database import get_db


def create_backup(backup_type: str = "manual") -> dict:
    data_dir = Path(settings.database_path).parent
    backup_dir = data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = Path(settings.database_path)

    # Backup database
    db_backup = backup_dir / f"assistant_{timestamp}.db"
    shutil.copy2(db_path, db_backup)

    # Backup uploads
    uploads_dir = Path(settings.uploads_dir)
    uploads_backup = backup_dir / f"uploads_{timestamp}"
    if uploads_dir.exists():
        shutil.copytree(uploads_dir, uploads_backup, dirs_exist_ok=True)

    # Record backup
    size = db_backup.stat().st_size
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO backups (path, size_bytes, type, status) VALUES (?, ?, ?, ?)",
            (str(db_backup), size, backup_type, "completed"),
        )
        backup_id = cur.lastrowid

    return {"id": backup_id, "path": str(db_backup), "size_bytes": size, "type": backup_type}


def list_backups(limit: int = 20, offset: int = 0) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM backups ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
    return [dict(r) for r in rows]


def restore_backup(backup_id: int) -> dict:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM backups WHERE id = ?", (backup_id,)).fetchone()
    if not row:
        return {"error": "Backup not found"}

    db_path = Path(settings.database_path)
    backup_path = Path(row["path"])

    if not backup_path.exists():
        return {"error": "Backup file not found"}

    # Close all connections by copying over the file
    shutil.copy2(backup_path, db_path)

    return {"success": True, "restored_from": str(backup_path)}
