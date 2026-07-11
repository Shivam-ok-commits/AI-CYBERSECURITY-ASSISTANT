import json
import yaml

with open(r'C:\Users\dell\.local\share\opencode\tool-output\tool_f508932c20016snBHw566fHGPl', 'r') as f:
    schema = json.load(f)

with open('openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)

with open('openapi.yaml', 'w') as f:
    yaml.dump(schema, f, default_flow_style=False, sort_keys=False, width=120)

print(f'Written openapi.json ({len(json.dumps(schema))} bytes)')
print(f'Written openapi.yaml')
print(f'Paths: {len(schema["paths"])}')
print(f'Schemas: {len(schema["components"].get("schemas", {}))}')
