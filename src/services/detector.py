import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

ENCODED_PS_RE = re.compile(
    r"""[-/]e(?:ncod(?:ed)?c(?:ommand)?)?\s+['"]?([A-Za-z0-9+/=]{40,})['"]?""",
    re.IGNORECASE,
)
BASE64_PS_RE = re.compile(r"(?:[A-Za-z0-9+/=]{80,})")
SUSPICIOUS_PAIRS: list[tuple[str, str]] = [
    ("cmd.exe", "powershell.exe"),
    ("cmd.exe", "pwsh.exe"),
    ("powershell.exe", "rundll32.exe"),
    ("explorer.exe", "cmd.exe"),
    ("winword.exe", "powershell.exe"),
    ("excel.exe", "cmd.exe"),
    ("rundll32.exe", "regsvr32.exe"),
]
OUTBOUND_PORTS = {21, 22, 23, 3389, 4444, 1337, 445, 1433, 3306, 5900, 8080}
PERSISTENCE_PATTERNS = [
    r"run\s+key", r"currentversion\\run", r"scheduled.?task",
    r"startup\s+folder", r"service\s+installed", r"systemd\s+service",
    r"cron\s+job", r"autorun", r"registry.*run",
    r"schtasks", r"at\s+command",
]
PRIVILEGE_ESC_PATTERNS = [
    "sudo", "su ", "runas",  "admin", "elevated",
    "seprivilege", "token elevation", "sebackupprivilege",
]
EVENT_IDS_PRIV_ESC = ["4672", "4673", "4732", "4733", "4756"]


def detect_suspicious_events(events: list[dict]) -> list[dict]:
    findings: list[dict] = []
    findings.extend(_detect_encoded_powershell(events))
    findings.extend(_detect_suspicious_process_pairs(events))
    findings.extend(_detect_persistence(events))
    findings.extend(_detect_privilege_escalation(events))
    return findings


def detect_brute_force(events: list[dict], threshold: int = 5, window_minutes: int = 5) -> list[dict]:
    failed = [e for e in events if e.get("event_name") == "failed_login"]
    ip_groups: dict[str, list[datetime | str]] = defaultdict(list)
    for ev in failed:
        ts = ev.get("timestamp")
        ip = ev.get("source_ip") or "unknown"
        if ts:
            ip_groups[ip].append(ts)

    findings: list[dict] = []
    for ip, timestamps in ip_groups.items():
        if len(timestamps) < threshold:
            continue
        parsed = []
        for t in timestamps:
            try:
                for fmt in ("%b %d %H:%M:%S", "%d/%b/%Y:%H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y %H:%M:%S"):
                    try:
                        parsed.append(datetime.strptime(t[:19], fmt))
                        break
                    except ValueError:
                        continue
            except (ValueError, TypeError):
                pass
        if len(parsed) < threshold:
            continue
        parsed.sort()
        for i in range(len(parsed) - threshold + 1):
            window = parsed[i + threshold - 1] - parsed[i]
            if window <= timedelta(minutes=window_minutes):
                findings.append({
                    "type": "brute_force",
                    "label": f"Brute-Force Attack ({threshold}+ failed logins in {window_minutes}m)",
                    "source_ip": ip,
                    "count": len(timestamps),
                    "severity": "critical",
                    "details": f"{len(timestamps)} failed logins from {ip}",
                })
                break
    return findings


def _detect_encoded_powershell(events: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for ev in events:
        raw = ev.get("raw", "")
        if ENCODED_PS_RE.search(raw) or (BASE64_PS_RE.search(raw) and "powershell" in raw.lower()):
            findings.append({
                "type": "encoded_powershell",
                "label": "Encoded PowerShell Command",
                "source_ip": ev.get("source_ip"),
                "severity": "high",
                "details": raw[:200],
                "line_number": ev.get("line_number"),
            })
    return findings


def _detect_suspicious_process_pairs(events: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for ev in events:
        raw = (ev.get("raw") or "").lower()
        if ev.get("event_name") == "process_creation":
            for parent, child in SUSPICIOUS_PAIRS:
                if parent in raw and child in raw:
                    findings.append({
                        "type": "suspicious_process_pair",
                        "label": f"Suspicious Process Chain: {parent} → {child}",
                        "source_ip": ev.get("source_ip"),
                        "severity": "high",
                        "details": raw[:200],
                        "line_number": ev.get("line_number"),
                    })
                    break
    return findings


def _detect_persistence(events: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for ev in events:
        raw = (ev.get("raw") or "").lower()
        if ev.get("event_name") in ("service_creation", "registry_modification", "file_creation"):
            for pat in PERSISTENCE_PATTERNS:
                if re.search(pat, raw):
                    findings.append({
                        "type": "persistence",
                        "label": f"Persistence Indicator: {ev.get('event_label', 'Unknown')}",
                        "source_ip": ev.get("source_ip"),
                        "severity": "high",
                        "details": raw[:200],
                        "line_number": ev.get("line_number"),
                    })
                    break
    return findings


def _detect_privilege_escalation(events: list[dict]) -> list[dict]:
    findings: list[dict] = []
    for ev in events:
        raw = (ev.get("raw") or "").lower()
        ev_type = (ev.get("event_type") or "").lower()
        if ev_type in [e.lower() for e in EVENT_IDS_PRIV_ESC]:
            findings.append({
                "type": "privilege_escalation",
                "label": "Privilege Escalation Detected",
                "source_ip": ev.get("source_ip"),
                "severity": "critical",
                "details": raw[:200],
                "line_number": ev.get("line_number"),
            })
            continue
        for pat in PRIVILEGE_ESC_PATTERNS:
            if pat.lower() in raw:
                findings.append({
                    "type": "privilege_escalation",
                    "label": f"Privilege Escalation: '{pat}'",
                    "source_ip": ev.get("source_ip"),
                    "severity": "high",
                    "details": raw[:200],
                    "line_number": ev.get("line_number"),
                })
                break
    return findings
