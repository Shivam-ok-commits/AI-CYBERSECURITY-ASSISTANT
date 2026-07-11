import json

with open(r'C:\Users\dell\.local\share\opencode\tool-output\tool_f508932c20016snBHw566fHGPl', 'r') as f:
    schema = json.load(f)

paths = schema.get('paths', {})

# Check endpoints that take raw string params
for ep in ['/api/v1/detection/sigma/validate', '/api/v1/detection/ai/generate-sigma', 
           '/api/v1/detection/ai/generate-yara', '/api/v1/detection/ai/explain',
           '/api/v1/detection/ai/improve', '/api/v1/detection/yara/validate',
           '/api/v1/detection/sigma/{rule_id}/execute',
           '/api/v1/detection/yara/{rule_id}/scan',
           '/api/v1/detection/rules/{rule_id}/test']:
    if ep in paths:
        for method, details in paths[ep].items():
            params = details.get('parameters', [])
            req = details.get('requestBody', {})
            names = [p["name"] for p in params]
            has_body = bool(req)
            body_schema = req.get('content', {}).get('application/json', {}).get('schema', {}) if has_body else {}
            print(f'{method.upper()} {ep}')
            print(f'  parameters: {names}')
            print(f'  requestBody: {has_body}')
            if has_body:
                print(f'  body schema: {json.dumps(body_schema)}')
            print()

# Check for 204 No Content endpoints
print('=== 204 No Content ===')
for path, methods in paths.items():
    for method, details in methods.items():
        responses = details.get('responses', {})
        for code, resp in responses.items():
            if code == '204':
                print(f'{method.upper()} {path}')

print()
print('=== Summary ===')
total = sum(len(methods) for methods in paths.values())
empty_schemas = 0
for path, methods in paths.items():
    for method, details in methods.items():
        for code, resp in details.get('responses', {}).items():
            content = resp.get('content', {})
            for ct, ct_det in content.items():
                if ct_det.get('schema', {}) == {}:
                    empty_schemas += 1

print(f'Total paths: {len(paths)}')
print(f'Total operations: {total}')
print(f'Empty response schemas: {empty_schemas}')
