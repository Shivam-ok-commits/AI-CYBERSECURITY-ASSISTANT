from collections import defaultdict


def build_timeline(events: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)

    for ev in events:
        ts = ev.get("timestamp") or "unknown"
        grouped[ts].append(ev)

    timeline = []
    for ts, entries in sorted(grouped.items(), key=lambda x: (x[0] == "unknown", x[0])):
        critical_count = sum(1 for e in entries if e.get("severity") in ("critical", "high"))
        timeline.append({
            "timestamp": ts,
            "event_count": len(entries),
            "critical_count": critical_count,
            "is_critical": critical_count > 0,
            "entries": entries[:20],
        })
    return timeline


def get_attack_chain(timeline: list[dict]) -> list[str]:
    phases = []
    has_recon = False
    has_access = False
    has_exec = False
    has_persist = False

    for block in timeline:
        for entry in block.get("entries", []):
            name = entry.get("event_name", "")
            if name == "failed_login" and not has_recon:
                phases.append("Reconnaissance / Brute-Force")
                has_recon = True
            if name == "successful_login" and not has_access:
                phases.append("Initial Access")
                has_access = True
            if name == "process_creation" and not has_exec:
                phases.append("Execution")
                has_exec = True
            if name == "service_creation" and not has_persist:
                phases.append("Persistence")
                has_persist = True

    if not phases:
        phases.append("No attack chain identified")
    return phases
