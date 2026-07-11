import json

with open('openapi.json', 'r') as f:
    schema = json.load(f)

schemas = schema['components']['schemas']

# Build type name mapping - remove 'Response', 'Request', 'Create', etc for cleaner names
# But use the exact schema names as interfaces

output = []
output.append('// Auto-generated from OpenAPI schema -- do not edit manually')
output.append(f'// Generated: 2026-07-11')
output.append(f'// Source: openapi.json ({len(schemas)} schemas)')
output.append('')

# Helper to convert OpenAPI type to TS type
def oa_to_ts(ptype):
    m = {
        'string': 'string',
        'integer': 'number',
        'number': 'number',
        'boolean': 'boolean',
        'object': 'Record<string, unknown>',
        'array': 'unknown[]',
        'any': 'unknown',
    }
    return m.get(ptype, 'unknown')

def schema_name_to_interface(name):
    if name == 'HTTPValidationError':
        return None  # skip built-in
    if name.startswith('Body_'):
        return None  # skip upload body
    return name

# Track which schemas to skip
skip_schemas = {'HTTPValidationError', 'ValidationError', 'Body_upload_log_api_v1_logs_upload_post'}
skip_prefixes = ('Body_',)

processed = []
for name in sorted(schemas.keys()):
    if name in skip_schemas:
        continue
    if name.startswith(skip_prefixes):
        continue
    
    s = schemas[name]
    props = s.get('properties', {})
    required = set(s.get('required', []))
    
    output.append(f'export interface {name} {{')
    for pn in sorted(props.keys()):
        pv = props[pn]
        opt = '' if pn in required else '?'
        ref = pv.get('$ref', '')
        ptype = pv.get('type', '')
        items = pv.get('items', {})
        iref = items.get('$ref', '') if items else ''
        
        if ref:
            ref_name = ref.split('/')[-1]
            output.append(f'  {pn}{opt}: {ref_name};')
        elif ptype == 'array':
            if iref:
                ref_name = iref.split('/')[-1]
                output.append(f'  {pn}{opt}: {ref_name}[];')
            else:
                it = items.get('type', 'any')
                if it == 'object' or it == 'any':
                    output.append(f'  {pn}{opt}: Record<string, unknown>[];')
                else:
                    output.append(f'  {pn}{opt}: {oa_to_ts(it)}[];')
        elif ptype == 'object':
            output.append(f'  {pn}{opt}: Record<string, unknown>;')
        elif ptype:
            ts_type = oa_to_ts(ptype)
            output.append(f'  {pn}{opt}: {ts_type};')
        else:
            # Type not specified (nullable/optional field)
            output.append(f'  {pn}{opt}: unknown;')
    output.append('}')
    output.append('')
    processed.append(name)

with open('frontend/src/types/api.ts', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))
    f.write(f'\n// Generated {len(processed)} interfaces\n')
