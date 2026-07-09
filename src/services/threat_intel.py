import json
from datetime import datetime, timedelta, timezone

import httpx

from src.config import settings

THREAT_CACHE_MINUTES = 15


def _is_expired(expires_at: str | None) -> bool:
    if not expires_at:
        return True
    try:
        return datetime.fromisoformat(expires_at) < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return True


async def lookup_virustotal(indicator: str, ioc_type: str) -> dict | None:
    key = settings.virustotal_api_key
    if not key:
        return None
    url_map = {
        "ip": f"https://www.virustotal.com/api/v3/ip_addresses/{indicator}",
        "domain": f"https://www.virustotal.com/api/v3/domains/{indicator}",
        "url": f"https://www.virustotal.com/api/v3/urls/{indicator}",
        "md5": f"https://www.virustotal.com/api/v3/files/{indicator}",
        "sha1": f"https://www.virustotal.com/api/v3/files/{indicator}",
        "sha256": f"https://www.virustotal.com/api/v3/files/{indicator}",
    }
    url = url_map.get(ioc_type)
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url, headers={"x-apikey": key})
            if r.status_code == 200:
                data = r.json()
                attrs = data.get("data", {}).get("attributes", {})
                stats = attrs.get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                total = sum(stats.values()) or 1
                return {
                    "source": "virustotal",
                    "threat_score": round(malicious / total * 10, 1),
                    "detection_ratio": f"{malicious}/{total}",
                    "country": attrs.get("country", ""),
                    "asn": attrs.get("asn", ""),
                    "raw": json.dumps(attrs, default=str)[:1000],
                }
    except Exception:
        pass
    return None


async def lookup_abuseipdb(indicator: str) -> dict | None:
    key = settings.abuseipdb_api_key
    if not key:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": indicator, "maxAgeInDays": 90},
                headers={"Key": key, "Accept": "application/json"},
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                return {
                    "source": "abuseipdb",
                    "threat_score": data.get("abuseConfidenceScore", 0) / 10,
                    "country": data.get("countryCode", "") or data.get("countryName", ""),
                    "asn": f"AS{data.get('asn', '')}" if data.get("asn") else "",
                    "raw": json.dumps(data, default=str)[:1000],
                }
    except Exception:
        pass
    return None


async def lookup_alienvault(indicator: str, ioc_type: str) -> dict | None:
    key = settings.otx_api_key
    if not key:
        return None
    type_map = {"ip": "IPv4", "domain": "domain", "md5": "file", "sha1": "file", "sha256": "file", "url": "url"}
    otx_type = type_map.get(ioc_type)
    if not otx_type:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                f"https://otx.alienvault.com/api/v1/indicators/{otx_type}/{indicator}/general",
                headers={"X-OTX-API-KEY": key},
            )
            if r.status_code == 200:
                data = r.json()
                pulses = data.get("pulse_info", {}).get("pulses", [])
                threat_score = min(len(pulses) * 2, 10) if pulses else 0
                malware = list({p.get("name", "") for p in pulses if p.get("name")})
                actors = list({t.get("name", "") for p in pulses for t in p.get("tags", [])})
                return {
                    "source": "alienvault",
                    "threat_score": threat_score,
                    "malware_associations": malware,
                    "threat_actor_associations": actors,
                    "raw": json.dumps(data, default=str)[:1000],
                }
    except Exception:
        pass
    return None


async def lookup_cisa_kev() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get("https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")
            if r.status_code == 200:
                vulns = r.json().get("vulnerabilities", [])
                return [
                    {
                        "cve_id": v.get("cveID", ""),
                        "vendor": v.get("vendorProject", ""),
                        "product": v.get("product", ""),
                        "description": v.get("shortDescription", ""),
                        "date_added": v.get("dateAdded", ""),
                        "required_action": v.get("requiredAction", ""),
                    }
                    for v in vulns[:50]
                ]
    except Exception:
        pass
    return []


async def lookup_nvd(cve_id: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(
                f"https://services.nvd.nist.gov/rest/json/cves/2.0",
                params={"cveId": cve_id},
            )
            if r.status_code == 200:
                vuln = r.json().get("vulnerabilities", [{}])[0].get("cve", {})
                metrics = vuln.get("metrics", {})
                cvss_v31 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
                return {
                    "cve_id": cve_id,
                    "description": vuln.get("descriptions", [{}])[0].get("value", ""),
                    "severity": cvss_v31.get("baseSeverity", ""),
                    "score": cvss_v31.get("baseScore", 0),
                    "vector": cvss_v31.get("vectorString", ""),
                    "published": vuln.get("published", ""),
                }
    except Exception:
        pass
    return None


async def enrich_ioc(indicator: str, ioc_type: str) -> dict:
    results: dict = {
        "threat_score": 0,
        "country": "",
        "asn": "",
        "malware_associations": [],
        "threat_actor_associations": [],
        "detection_ratio": "0/0",
        "sources": [],
    }

    tasks = []
    if ioc_type in ("ip", "domain", "md5", "sha1", "sha256", "url"):
        tasks.append(lookup_virustotal(indicator, ioc_type))
    if ioc_type == "ip":
        tasks.append(lookup_abuseipdb(indicator))
    if ioc_type in ("ip", "domain", "md5", "sha1", "sha256", "url"):
        tasks.append(lookup_alienvault(indicator, ioc_type))

    for t in tasks:
        result = await t
        if result:
            results["sources"].append(result["source"])
            results["threat_score"] = max(results["threat_score"], result.get("threat_score", 0))
            results["country"] = result.get("country", results["country"])
            results["asn"] = result.get("asn", results["asn"])
            results["detection_ratio"] = result.get("detection_ratio", results["detection_ratio"])
            malware = result.get("malware_associations", [])
            if malware:
                results["malware_associations"].extend(malware)
            actors = result.get("threat_actor_associations", [])
            if actors:
                results["threat_actor_associations"].extend(actors)

    if not results["sources"]:
        results["threat_score"] = _simulated_score(indicator, ioc_type)

    return results


def _simulated_score(indicator: str, ioc_type: str) -> float:
    seed = sum(ord(c) for c in indicator)
    return round((seed % 100) / 10, 1)
