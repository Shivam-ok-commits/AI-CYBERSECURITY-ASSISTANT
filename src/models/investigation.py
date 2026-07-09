from dataclasses import dataclass


@dataclass
class Investigation:
    id: int
    user_id: int
    title: str
    description: str
    status: str
    severity: str
    findings: str
    created_at: str
    updated_at: str
