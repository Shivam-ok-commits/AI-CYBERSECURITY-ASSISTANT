import urllib.request, json

BASE = 'http://127.0.0.1:8765/api/v1'
TOKEN = None

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
        return e.code, json.loads(e.read().decode())

# Get token
code, data = req('POST', '/auth/login', {'username': 'auditbot', 'password': 'auditpass'})
TOKEN = data.get('access_token', '')

# Check more endpoints
endpoints = [
    ('GET', '/threat/extract/1', 'Extract from log (404 expected)', {'token': True}),
    ('GET', '/threat/correlate/global', 'Correlate global', {'token': True}),
    ('POST', '/detection/analytics/hit?rule_type=test&rule_id=1&severity=medium', 'Analytics hit', {'token': True}),
    ('POST', '/detection/sigma/validate', 'Validate sigma', {'content': 'test'}),
    ('POST', '/detection/yara/validate', 'Validate yara', {'content': 'test'}),
    ('GET', '/enterprise/plans', 'Plans', {}),
    ('GET', '/dashboard/notifications/unread-count', 'Unread count', {'token': True}),
    ('GET', '/cases/search/find?query=test', 'Search cases', {'token': True}),
    ('POST', '/ai/explain', 'Explain', {'data': {'text': 'What is SQL injection?'}}),
    ('POST', '/ai/providers/switch', 'Switch provider', {'data': {'provider': 'openai'}}),
]

for method, path, desc, opts in endpoints:
    token = TOKEN if opts.get('token') else None
    data = opts.get('data', None)
    code, resp = req(method, path, data, token)
    rtype = type(resp).__name__
    shape = {}
    if isinstance(resp, dict):
        shape = {k: type(v).__name__ for k, v in resp.items()}
    elif isinstance(resp, list) and resp:
        if isinstance(resp[0], dict):
            shape = list(resp[0].keys())
    
    sample = json.dumps(resp, indent=2, ensure_ascii=False)[:500]
    print(f'{method:6s} {code:3d} {desc:40s} -> {rtype} keys={list(shape.keys())[:10]}')
    print(f'  sample: {sample[:300]}')
    print()
