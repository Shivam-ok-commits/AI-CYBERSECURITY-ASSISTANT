import urllib.request, json, sys

BASE = 'http://127.0.0.1:8765/api/v1'

def req(method, path, data=None, token=None):
    url = BASE + path
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"raw": body[:500]}

results = []

def probe(method, path, desc, data=None, token=None):
    code, resp = req(method, path, data, token)
    rtype = type(resp).__name__
    rshape = {}
    if isinstance(resp, dict):
        rshape = {k: type(v).__name__ for k, v in resp.items()}
        sample = json.dumps(resp, indent=2)[:300]
    elif isinstance(resp, list):
        if resp:
            rshape = {k: type(v).__name__ for k, v in resp[0].items()} if isinstance(resp[0], dict) else {"items": type(resp[0]).__name__}
        sample = json.dumps(resp[:2], indent=2)[:300]
    else:
        sample = str(resp)[:300]
    results.append({"method": method, "path": path, "desc": desc, "code": code, "type": rtype, "shape": rshape, "sample": sample})
    print(f'{method:6s} {code:3d} {desc[:50]:50s} -> {rtype} ({len(rshape)} keys)')

# Anonymous endpoints
probe('GET', '/health', 'Health check')

# Auth
code, reg_resp = req('POST', '/auth/register', {'username': 'auditbot', 'password': 'auditpass'})
TOKEN = reg_resp.get('access_token', '')

probe('POST', '/auth/login', 'Login', {'username': 'auditbot', 'password': 'auditpass'})
probe('GET', '/auth/me', 'Get profile', token=TOKEN)
probe('GET', '/auth/admin-only', 'Admin only', token=TOKEN)

# Logs
probe('GET', '/logs/', 'List logs', token=TOKEN)
probe('GET', '/logs/stats/global', 'Global stats', token=TOKEN)

# Threat Intel
probe('POST', '/threat/extract', 'Extract IOCs', {'text': '1.2.3.4 evil.com malware.exe'})
probe('GET', '/threat/lookup?indicator=8.8.8.8&type=ip', 'Lookup IOC')
probe('GET', '/threat/iocs', 'List IOCs', token=TOKEN)
probe('GET', '/threat/iocs/stats', 'IOC stats')
probe('GET', '/threat/cisa-kev', 'CISA KEV')
probe('GET', '/threat/feed', 'Threat feed')
probe('GET', '/threat/feed/daily', 'Daily feed')
probe('POST', '/threat/correlate', 'Correlate IOCs', {'iocs': ['1.2.3.4', 'evil.com']}, token=TOKEN)

# AI
probe('GET', '/ai/providers', 'AI providers')
probe('GET', '/ai/providers/active', 'Active provider')
probe('GET', '/ai/prompts', 'AI prompts')
probe('GET', '/ai/sessions', 'List sessions', token=TOKEN)

# Dashboard
probe('GET', '/dashboard/executive', 'Executive summary')
probe('GET', '/dashboard/summary', 'Dashboard summary', token=TOKEN)
probe('GET', '/dashboard/alerts', 'List alerts')
probe('GET', '/dashboard/alerts/stats', 'Alert stats')
probe('GET', '/dashboard/logs/stats', 'Log stats')
probe('GET', '/dashboard/threat/stats', 'Threat stats')
probe('GET', '/dashboard/investigations/stats', 'Investigation stats')
probe('GET', '/dashboard/charts/severity', 'Severity chart')
probe('GET', '/dashboard/charts/attack-timeline?days=7', 'Attack timeline')
probe('GET', '/dashboard/charts/threat-distribution', 'Threat distribution')
probe('GET', '/dashboard/charts/ioc-trend?days=30', 'IOC trend')
probe('GET', '/dashboard/charts/cve-trend?days=30', 'CVE trend')
probe('GET', '/dashboard/charts/event-types', 'Event types chart')
probe('GET', '/dashboard/settings', 'Settings', token=TOKEN)
probe('GET', '/dashboard/users/analysts', 'List analysts', token=TOKEN)
probe('GET', '/dashboard/users/activity', 'User activity', token=TOKEN)

# Case Management
probe('GET', '/cases/templates', 'List templates')
probe('GET', '/cases/archived/list', 'Archived cases', token=TOKEN)
probe('GET', '/cases/audit/logs', 'Audit logs', token=TOKEN)

# Detection
probe('GET', '/detection/rules', 'List rules')
probe('GET', '/detection/sigma', 'List sigma')
probe('GET', '/detection/yara', 'List yara')
probe('GET', '/detection/hunts', 'List hunts', token=TOKEN)
probe('GET', '/detection/hunts/results', 'Hunt results', token=TOKEN)
probe('GET', '/detection/analytics', 'Analytics')
probe('GET', '/detection/playbooks', 'List playbooks')
probe('GET', '/detection/reports', 'List reports', token=TOKEN)
probe('GET', '/detection/jobs', 'List jobs', token=TOKEN)
probe('GET', '/detection/automation', 'List automation')

# Enterprise
probe('GET', '/enterprise/notifications', 'List notifications', token=TOKEN)
probe('GET', '/enterprise/orgs', 'List orgs', token=TOKEN)
probe('GET', '/enterprise/plans', 'Plans')
probe('GET', '/enterprise/metrics', 'Metrics')
probe('GET', '/enterprise/metrics/stats', 'Metrics stats')
probe('GET', '/enterprise/backups', 'Backups')

# Plugins
probe('GET', '/plugins/', 'List plugins', token=TOKEN)

print("\n=== DEEP RESPONSE INSPECTION ===")
print(json.dumps(results, indent=2))
