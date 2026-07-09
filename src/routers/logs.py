import json
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status

from src.config import settings
from src.database import get_db
from src.schemas.log import (
    ExtractedEvent,
    LogDetail,
    LogEntry,
    StatsResponse,
    SuspiciousFinding,
    TimelineBlock,
    UploadLogResponse,
)
from src.services.auth import get_current_user
from src.services.detector import detect_brute_force, detect_suspicious_events
from src.services.event_extractor import extract_events
from src.services.log_parser import detect_source_type, parse_log, validate_file
from src.services.statistics import compute_stats
from src.services.timeline import build_timeline, get_attack_chain

router = APIRouter(prefix="/logs", tags=["logs"])


def _get_log_events(log_id: int, user_id: int) -> list[dict]:
    with get_db() as conn:
        log = conn.execute("SELECT id FROM uploaded_logs WHERE id = ? AND user_id = ?", (log_id, user_id)).fetchone()
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
        rows = conn.execute(
            "SELECT * FROM parsed_events WHERE log_id = ? ORDER BY line_number",
            (log_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Upload ──

@router.post("/upload", response_model=UploadLogResponse, status_code=status.HTTP_201_CREATED)
def upload_log(file: UploadFile, user: dict = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    content = file.file.read()
    size = len(content)

    try:
        validate_file(file.filename, size)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    text = content.decode("utf-8", errors="replace")
    sample = text[:500]
    source_type = detect_source_type(sample, file.filename)
    events = parse_log(text, source_type)

    os.makedirs(settings.uploads_dir, exist_ok=True)
    dest = os.path.join(settings.uploads_dir, f"{user['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
    with open(dest, "wb") as f:
        f.write(content)

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO uploaded_logs (user_id, filename, filepath, size_bytes, source_type, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], file.filename, dest, size, source_type, "parsed"),
        )
        log_id = cur.lastrowid

        for ev in events:
            conn.execute(
                "INSERT INTO parsed_events (log_id, line_number, timestamp, source_ip, event_type, severity, raw, parsed_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (log_id, ev["line_number"], ev["timestamp"], ev["source_ip"], ev["event_type"], ev["severity"], ev["raw"], json.dumps(ev)),
            )

    return UploadLogResponse(id=log_id, filename=file.filename, size_bytes=size, source_type=source_type, status="parsed", event_count=len(events))


# ── List ──

@router.get("/", response_model=list[LogDetail])
def list_logs(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT l.*, (SELECT COUNT(*) FROM parsed_events WHERE log_id = l.id) AS event_count
               FROM uploaded_logs l WHERE l.user_id = ? ORDER BY l.created_at DESC""",
            (user["id"],),
        ).fetchall()
    return [
        LogDetail(id=r["id"], filename=r["filename"], source_type=r["source_type"], status=r["status"], size_bytes=r["size_bytes"], event_count=r["event_count"], created_at=r["created_at"])
        for r in rows
    ]


# ── Log detail ──

@router.get("/{log_id}", response_model=LogDetail)
def get_log(log_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        row = conn.execute(
            """SELECT l.*, (SELECT COUNT(*) FROM parsed_events WHERE log_id = l.id) AS event_count
               FROM uploaded_logs l WHERE l.id = ? AND l.user_id = ?""",
            (log_id, user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return LogDetail(id=row["id"], filename=row["filename"], source_type=row["source_type"], status=row["status"], size_bytes=row["size_bytes"], event_count=row["event_count"], created_at=row["created_at"])


# ── Raw events ──

@router.get("/{log_id}/events", response_model=list[LogEntry])
def get_events(log_id: int, user: dict = Depends(get_current_user)):
    rows = _get_log_events(log_id, user["id"])
    return [LogEntry(**r) for r in rows]


@router.get("/{log_id}/events.json")
def get_events_json(log_id: int, user: dict = Depends(get_current_user)):
    return _get_log_events(log_id, user["id"])


# ── Extracted events ──

@router.get("/{log_id}/extracted", response_model=list[ExtractedEvent])
def get_extracted_events(log_id: int, user: dict = Depends(get_current_user)):
    rows = _get_log_events(log_id, user["id"])
    return extract_events(rows)


# ── Suspicious ──

@router.get("/{log_id}/suspicious", response_model=list[SuspiciousFinding])
def get_suspicious(
    log_id: int,
    user: dict = Depends(get_current_user),
    brute_force_threshold: int = Query(5, alias="bf-threshold"),
    brute_force_window: int = Query(5, alias="bf-window"),
):
    rows = _get_log_events(log_id, user["id"])
    extracted = extract_events(rows)
    findings = detect_suspicious_events(extracted)
    findings.extend(detect_brute_force(extracted, brute_force_threshold, brute_force_window))
    return findings


# ── Timeline ──

@router.get("/{log_id}/timeline", response_model=list[TimelineBlock])
def get_timeline(log_id: int, user: dict = Depends(get_current_user)):
    rows = _get_log_events(log_id, user["id"])
    extracted = extract_events(rows)
    return build_timeline(extracted)


@router.get("/{log_id}/attack-chain")
def get_attack_chain_endpoint(log_id: int, user: dict = Depends(get_current_user)):
    rows = _get_log_events(log_id, user["id"])
    extracted = extract_events(rows)
    timeline = build_timeline(extracted)
    return {"attack_chain": get_attack_chain(timeline)}


# ── Statistics ──

@router.get("/{log_id}/statistics", response_model=StatsResponse)
def get_statistics(
    log_id: int,
    user: dict = Depends(get_current_user),
    brute_force_threshold: int = Query(5, alias="bf-threshold"),
    brute_force_window: int = Query(5, alias="bf-window"),
):
    rows = _get_log_events(log_id, user["id"])
    extracted = extract_events(rows)
    suspicious = detect_suspicious_events(extracted)
    suspicious.extend(detect_brute_force(extracted, brute_force_threshold, brute_force_window))
    return compute_stats(extracted, suspicious)


# ── Global statistics (across all user logs) ──

@router.get("/stats/global", response_model=StatsResponse)
def global_statistics(
    user: dict = Depends(get_current_user),
    brute_force_threshold: int = Query(5, alias="bf-threshold"),
    brute_force_window: int = Query(5, alias="bf-window"),
):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT e.* FROM parsed_events e JOIN uploaded_logs l ON e.log_id = l.id WHERE l.user_id = ? ORDER BY e.line_number",
            (user["id"],),
        ).fetchall()
    all_events = [dict(r) for r in rows]
    extracted = extract_events(all_events)
    suspicious = detect_suspicious_events(extracted)
    suspicious.extend(detect_brute_force(extracted, brute_force_threshold, brute_force_window))
    return compute_stats(extracted, suspicious)
