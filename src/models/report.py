from dataclasses import dataclass


@dataclass
class Report:
    id: int
    user_id: int
    investigation_id: int | None
    title: str
    content: str
    format: str
    created_at: str
