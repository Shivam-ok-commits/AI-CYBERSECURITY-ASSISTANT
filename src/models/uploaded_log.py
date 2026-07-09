from dataclasses import dataclass


@dataclass
class UploadedLog:
    id: int
    user_id: int
    filename: str
    filepath: str
    size_bytes: int
    source_type: str
    status: str
    created_at: str
