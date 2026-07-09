from collections import Counter


def compute_stats(events: list[dict], suspicious: list[dict]) -> dict:
    total = len(events)
    severity_counts: dict[str, int] = Counter()
    event_type_counts: dict[str, int] = Counter()
    ips: Counter = Counter()

    for ev in events:
        severity_counts[ev.get("severity", "info")] += 1
        event_type_counts[ev.get("event_type", "unknown")] += 1
        ip = ev.get("source_ip")
        if ip:
            ips[ip] += 1

    suspicious_count = len(suspicious)
    failed_login_count = sum(1 for e in events if e.get("event_name") == "failed_login")

    return {
        "total_events": total,
        "suspicious_events": suspicious_count,
        "failed_logins": failed_login_count,
        "severity_distribution": dict(severity_counts),
        "top_ips": [{"ip": ip, "count": c} for ip, c in ips.most_common(10)],
        "event_type_distribution": dict(event_type_counts),
    }
