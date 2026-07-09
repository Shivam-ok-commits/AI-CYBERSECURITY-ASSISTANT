import json
from datetime import datetime, timezone

from src.services.threat_intel import lookup_cisa_kev, lookup_nvd


async def get_daily_summary() -> dict:
    cisa = await lookup_cisa_kev()
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "known_exploited_vulnerabilities": cisa[:10],
        "total_kev": len(cisa),
    }


async def search_cves(query: str = "") -> list[dict]:
    try:
        import httpx
        params = {}
        if query:
            params["keywordSearch"] = query
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get("https://services.nvd.nist.gov/rest/json/cves/2.0", params=params)
            if r.status_code == 200:
                vulns = r.json().get("vulnerabilities", [])[:20]
                results = []
                for v in vulns:
                    cve = v.get("cve", {})
                    metrics = cve.get("metrics", {})
                    cvss = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
                    results.append({
                        "cve_id": cve.get("id", ""),
                        "description": cve.get("descriptions", [{}])[0].get("value", ""),
                        "severity": cvss.get("baseSeverity", ""),
                        "score": cvss.get("baseScore", 0),
                        "published": cve.get("published", ""),
                    })
                return results
    except Exception:
        pass
    return []


def generate_threat_feed() -> dict:
    return {
        "latest_cves": [],
        "latest_malware": [
            {"name": "Emotet", "type": "botnet", "risk": "critical", "date": "2026-07"},
            {"name": "LockBit", "type": "ransomware", "risk": "critical", "date": "2026-07"},
            {"name": "RedLine Stealer", "type": "infostealer", "risk": "high", "date": "2026-06"},
            {"name": "Black Basta", "type": "ransomware", "risk": "high", "date": "2026-06"},
        ],
        "latest_ransomware": [
            {"name": "LockBit 4.0", "group": "LockBit", "risk": "critical"},
            {"name": "BlackCat/ALPHV", "group": "ALPHV", "risk": "critical"},
        ],
        "latest_threat_actors": [
            {"name": "APT29 (Cozy Bear)", "country": "Russia", "sector": "government"},
            {"name": "Lazarus Group", "country": "North Korea", "sector": "finance"},
            {"name": "UNC1878", "country": "Unknown", "sector": "multiple"},
        ],
    }
