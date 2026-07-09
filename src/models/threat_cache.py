from dataclasses import dataclass


@dataclass
class ThreatCache:
    id: int
    indicator: str
    indicator_type: str
    threat_score: float
    source: str
    raw_data: str
    expires_at: str
    created_at: str
