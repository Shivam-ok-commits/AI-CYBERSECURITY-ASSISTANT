import json

with open('openapi.json', 'r') as f:
    schema = json.load(f)

schemas = schema['components']['schemas']

# Print all schemas with their properties in a machine-parseable format
for name in sorted(schemas.keys()):
    s = schemas[name]
    props = s.get('properties', {})
    required = set(s.get('required', []))
    ref = s.get('$ref', '')
    enum = s.get('enum', [])
    
    print(f"SCHEMA:{name}")
    if enum:
        print(f"  ENUM:{json.dumps(enum)}")
    for pn in sorted(props.keys()):
        pv = props[pn]
        is_req = "required" if pn in required else "optional"
        ref2 = pv.get('$ref', '')
        ptype = pv.get('type', '')
        items = pv.get('items', {})
        iref = items.get('$ref', '') if items else ''
        const = pv.get('const', '')
        
        if ref2:
            print(f"  {pn}:ref:{ref2.split('/')[-1]}:{is_req}")
        elif ptype == 'array' and iref:
            print(f"  {pn}:array:{iref.split('/')[-1]}:{is_req}")
        elif ptype == 'array':
            it = items.get('type', 'any')
            print(f"  {pn}:array:{it}:{is_req}")
        else:
            print(f"  {pn}:{ptype}:{is_req}")
    print()
