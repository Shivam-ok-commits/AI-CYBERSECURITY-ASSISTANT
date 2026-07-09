from collections import Counter, defaultdict

from src.database import get_db


def correlate_iocs(iocs: list[dict]) -> dict:
    indicators = [i["indicator"] for i in iocs]
    freq = Counter(indicators)
    log_groups: dict[str, set[int]] = defaultdict(set)

    for i in iocs:
        log_groups[i["indicator"]].add(i.get("log_id"))

    repeated = [{"indicator": k, "count": v, "logs": sorted(log_groups[k])} for k, v in freq.items() if v > 1]

    campaigns = _detect_campaigns(iocs, freq)

    return {
        "total_iocs": len(set(indicators)),
        "repeated_iocs": repeated,
        "campaigns": campaigns,
    }


def _detect_campaigns(iocs: list[dict], freq: Counter) -> list[dict]:
    campaigns: list[dict] = []
    ip_group = [i for i in iocs if i["indicator_type"] == "ip"]
    domain_group = [i for i in iocs if i["indicator_type"] == "domain"]
    hash_group = [i for i in iocs if i.get("indicator_type") in ("md5", "sha1", "sha256")]

    ip_set = {i["indicator"] for i in ip_group}
    domain_set = {i["indicator"] for i in domain_group}
    hash_set = {i["indicator"] for i in hash_group}

    if len(ip_set) >= 3:
        ips_detail = [{"ip": ip, "count": freq[ip]} for ip in list(ip_set)[:10]]
        campaigns.append({
            "name": "Multiple Suspicious IPs",
            "type": "ip_cluster",
            "indicators": ips_detail,
            "total_indicators": len(ip_set),
        })

    if len(hash_set) >= 2:
        campaigns.append({
            "name": "Multiple Malicious Hashes",
            "type": "hash_cluster",
            "indicators": [{"hash": h, "count": freq[h]} for h in list(hash_set)[:10]],
            "total_indicators": len(hash_set),
        })

    if ip_set and domain_set:
        campaigns.append({
            "name": "IP + Domain Campaign",
            "type": "ip_domain_correlation",
            "indicators": {
                "ips": list(ip_set)[:5],
                "domains": list(domain_set)[:5],
            },
        })

    return campaigns


def get_ioc_stats() -> dict:
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM ioc_reputation").fetchone()["c"]
        malicious = conn.execute("SELECT COUNT(*) AS c FROM ioc_reputation WHERE threat_score >= 5").fetchone()["c"]
        by_type = conn.execute(
            "SELECT indicator_type, COUNT(*) AS c FROM ioc_reputation GROUP BY indicator_type ORDER BY c DESC"
        ).fetchall()
    return {
        "total_iocs": total,
        "malicious_iocs": malicious,
        "by_type": [{"type": r["indicator_type"], "count": r["c"]} for r in by_type],
    }
