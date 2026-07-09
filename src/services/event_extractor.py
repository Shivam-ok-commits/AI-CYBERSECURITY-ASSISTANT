import re

EVENT_RULES: list[dict] = [
    {
        "name": "failed_login",
        "label": "Failed Login",
        "patterns": [
            "failed password", "authentication failure", "logon failure",
            "login failed", "failed logon", "invalid password",
        ],
        "event_ids": ["4625", "529", "534", "535", "539"],
    },
    {
        "name": "successful_login",
        "label": "Successful Login",
        "patterns": [
            "accepted password", "accepted publickey", "session opened",
            "successful logon", "logon success",
        ],
        "event_ids": ["4624", "528", "540"],
    },
    {
        "name":         "process_creation",
        "label": "Process Creation",
        "patterns": ["executed", "started", "created process", "new process", "process created", "process start", "process execute"],
        "event_ids": ["4688", "592"],
    },
    {
        "name": "file_creation",
        "label": "File Creation",
        "patterns": ["created file", "file create", "write file", "file written"],
        "event_ids": ["4663", "4656"],
    },
    {
        "name": "registry_modification",
        "label": "Registry Modification",
        "patterns": ["registry modification", "registry value set", "regedit"],
        "event_ids": ["4657"],
    },
    {
        "name": "network_connection",
        "label": "Network Connection",
        "patterns": ["connection from", "connected to", "outbound connection", "listening on"],
        "event_ids": ["5156", "5158", "5159"],
    },
    {
        "name": "service_creation",
        "label": "Service Creation",
        "patterns": ["service installed", "new service", "service created", "service started"],
        "event_ids": ["7045", "4697", "6011"],
    },
    {
        "name": "powershell_execution",
        "label": "PowerShell Execution",
        "patterns": ["powershell", "pwsh", "powerShell", "PowerShell", "-Command", "-File"],
        "event_ids": ["4104", "4103", "400", "403"],
    },
]


def extract_events(rows: list[dict]) -> list[dict]:
    results: list[dict] = []
    for row in rows:
        raw = (row.get("raw") or "").lower()
        ev_type = (row.get("event_type") or "").lower()
        for rule in EVENT_RULES:
            matched = False
            if ev_type in [e.lower() for e in rule["event_ids"]]:
                matched = True
            for pat in rule["patterns"]:
                if pat.lower() in raw:
                    matched = True
                    break
            if matched:
                results.append({
                    "event_name": rule["name"],
                    "event_label": rule["label"],
                    "line_number": row["line_number"],
                    "timestamp": row.get("timestamp"),
                    "source_ip": row.get("source_ip"),
                    "severity": row.get("severity", "info"),
                    "raw": row.get("raw", ""),
                })
                break
    return results
