import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.database import get_db
from src.schemas.threat_intel import (
    CVEResult,
    CorrelationResult,
    DailySummaryResponse,
    IOCDetailResponse,
    IOCExtractionResponse,
    IOCLookupResponse,
    IOCResult,
    IOCSearchResult,
    IOCStats,
    KEVResult,
    ThreatFeedResponse,
)
from src.services.auth import get_current_user
from src.services.ioc_correlation import correlate_iocs, get_ioc_stats
from src.services.ioc_extractor import extract_from_events, extract_iocs
from src.services.threat_feed import generate_threat_feed, get_daily_summary, search_cves
from src.services.threat_intel import enrich_ioc

router = APIRouter(prefix="/threat", tags=["threat-intel"])


def _get_db_ioc(indicator: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM ioc_reputation WHERE indicator = ?", (indicator,)).fetchone()
    return dict(row) if row else None


def _save_ioc(indicator: str, ioc_type: str, result: dict):
    expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO ioc_reputation
               (indicator, indicator_type, threat_score, source, country, asn,
                malware_associations, threat_actor_associations, detection_ratio, raw_data, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                indicator, ioc_type, result["threat_score"],
                ",".join(result.get("sources", [])),
                result.get("country", ""), result.get("asn", ""),
                json.dumps(result.get("malware_associations", [])),
                json.dumps(result.get("threat_actor_associations", [])),
                result.get("detection_ratio", "0/0"),
                json.dumps({k: v for k, v in result.items() if k != "sources"}, default=str),
                expires,
            ),
        )


# ── 4.1 IOC Extraction ──

@router.post("/extract", response_model=IOCExtractionResponse)
def extract_ioc_endpoint(text: str = Query(""), body: dict | None = None):
    if body:
        text = body.get("text") or text
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="text field required")
    return extract_iocs(text)


@router.get("/extract/{log_id}", response_model=list[dict])
def extract_from_log(log_id: int, user: dict = Depends(get_current_user)):
    from src.database import get_db
    with get_db() as conn:
        log = conn.execute("SELECT id FROM uploaded_logs WHERE id = ? AND user_id = ?", (log_id, user["id"])).fetchone()
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
        rows = conn.execute(
            "SELECT * FROM parsed_events WHERE log_id = ? ORDER BY line_number", (log_id,)
        ).fetchall()
    iocs = extract_from_events([dict(r) for r in rows])
    with get_db() as conn:
        for ioc in iocs:
            conn.execute(
                "INSERT OR IGNORE INTO ioc_correlations (indicator, indicator_type, log_id, event_line, context) VALUES (?, ?, ?, ?, ?)",
                (ioc["indicator"], ioc["indicator_type"], ioc.get("log_id"), ioc.get("event_line", 0), ioc.get("context", "")[:500]),
            )
    return iocs


# ── 4.2 IOC Lookup ──

@router.get("/lookup", response_model=IOCLookupResponse)
async def lookup_ioc(indicator: str = Query(...), type: str = Query("ip", alias="type")):
    valid_types = {"ip", "domain", "url", "md5", "sha1", "sha256", "email"}
    if type not in valid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid type. Must be one of: {', '.join(sorted(valid_types))}")

    cached = _get_db_ioc(indicator)
    if cached:
        expires = cached.get("expires_at")
        if expires and datetime.fromisoformat(expires) > datetime.now(timezone.utc):
            return IOCLookupResponse(
                indicator=indicator,
                indicator_type=type,
                reputation=IOCResult(
                    indicator=indicator,
                    indicator_type=type,
                    threat_score=cached["threat_score"],
                    country=cached["country"],
                    asn=cached["asn"],
                    malware_associations=json.loads(cached.get("malware_associations", "[]")),
                    threat_actor_associations=json.loads(cached.get("threat_actor_associations", "[]")),
                    detection_ratio=cached.get("detection_ratio", "0/0"),
                    sources=cached["source"].split(",") if cached["source"] else [],
                ),
            )

    result = await enrich_ioc(indicator, type)
    _save_ioc(indicator, type, result)

    return IOCLookupResponse(
        indicator=indicator,
        indicator_type=type,
        reputation=IOCResult(
            indicator=indicator,
            indicator_type=type,
            threat_score=result["threat_score"],
            country=result.get("country", ""),
            asn=result.get("asn", ""),
            malware_associations=result.get("malware_associations", []),
            threat_actor_associations=result.get("threat_actor_associations", []),
            detection_ratio=result.get("detection_ratio", "0/0"),
            sources=result.get("sources", []),
        ),
    )


# ── 4.3 Intelligence Sources ──

@router.get("/cisa-kev", response_model=list[KEVResult])
async def get_cisa_kev():
    from src.services.threat_intel import lookup_cisa_kev
    return await lookup_cisa_kev()


@router.get("/cve/{cve_id}", response_model=CVEResult)
async def get_cve(cve_id: str):
    from src.services.threat_intel import lookup_nvd
    result = await lookup_nvd(cve_id.upper())
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CVE not found")
    return result


@router.get("/nvd/search", response_model=list[CVEResult])
async def search_nvd(query: str = Query("", alias="q")):
    return await search_cves(query)


# ── 4.5 IOC Dashboard ──

@router.get("/iocs", response_model=list[IOCSearchResult])
def list_iocs(
    user: dict = Depends(get_current_user),
    search: str = Query("", alias="q"),
    ioc_type: str = Query("", alias="type"),
    min_score: float = Query(0, alias="min-score"),
    max_score: float = Query(10, alias="max-score"),
    skip: int = Query(0, alias="skip"),
    limit: int = Query(50, alias="limit"),
):
    with get_db() as conn:
        sql = "SELECT * FROM ioc_reputation WHERE threat_score >= ? AND threat_score <= ?"
        params: list = [min_score, max_score]
        if search:
            sql += " AND indicator LIKE ?"
            params.append(f"%{search}%")
        if ioc_type:
            sql += " AND indicator_type = ?"
            params.append(ioc_type)
        sql += " ORDER BY threat_score DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])
        rows = conn.execute(sql, params).fetchall()
    return [
        IOCSearchResult(id=r["id"], indicator=r["indicator"], indicator_type=r["indicator_type"], threat_score=r["threat_score"], source=r["source"], created_at=r["created_at"])
        for r in rows
    ]


@router.get("/iocs/stats", response_model=IOCStats)
def ioc_statistics():
    return get_ioc_stats()


@router.get("/iocs/{indicator}", response_model=IOCDetailResponse)
def get_ioc_detail(indicator: str):
    row = _get_db_ioc(indicator)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IOC not found")
    return IOCDetailResponse(
        indicator=row["indicator"],
        indicator_type=row["indicator_type"],
        threat_score=row["threat_score"],
        source=row["source"],
        country=row["country"],
        asn=row["asn"],
        malware_associations=json.loads(row.get("malware_associations", "[]")),
        threat_actor_associations=json.loads(row.get("threat_actor_associations", "[]")),
        detection_ratio=row.get("detection_ratio", "0/0"),
        first_seen=row.get("first_seen"),
        last_seen=row.get("last_seen"),
        created_at=row["created_at"],
    )


# ── 4.6 IOC Correlation ──

@router.get("/correlate/global", response_model=CorrelationResult)
def correlate_global(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT c.* FROM ioc_correlations c
               JOIN uploaded_logs l ON c.log_id = l.id
               WHERE l.user_id = ?""",
            (user["id"],),
        ).fetchall()
    if not rows:
        return CorrelationResult(total_iocs=0, repeated_iocs=[], campaigns=[])
    return correlate_iocs([dict(r) for r in rows])


@router.get("/correlate/{log_id}", response_model=CorrelationResult)
def correlate(log_id: int, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        log = conn.execute("SELECT id FROM uploaded_logs WHERE id = ? AND user_id = ?", (log_id, user["id"])).fetchone()
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
        rows = conn.execute("SELECT * FROM ioc_correlations WHERE log_id = ?", (log_id,)).fetchall()
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No IOCs extracted for this log. Run extract first.")
    return correlate_iocs([dict(r) for r in rows])


# ── 4.7 Threat Feed ──

@router.get("/feed", response_model=ThreatFeedResponse)
def threat_feed():
    return generate_threat_feed()


@router.get("/feed/daily", response_model=DailySummaryResponse)
async def daily_summary():
    return await get_daily_summary()
