from dataclasses import dataclass


@dataclass
class ParsedEvent:
    id: int
    log_id: int
    line_number: int
    timestamp: str | None
    source_ip: str | None
    event_type: str | None
    severity: str | None
    raw: str
    parsed_json: str
    created_at: str
