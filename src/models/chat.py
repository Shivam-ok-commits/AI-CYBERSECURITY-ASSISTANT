from dataclasses import dataclass


@dataclass
class Chat:
    id: int
    user_id: int
    session_id: str
    role: str
    content: str
    created_at: str
