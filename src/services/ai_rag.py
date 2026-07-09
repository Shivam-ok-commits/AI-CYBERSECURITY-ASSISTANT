import json
import re
from typing import Any

from src.database import get_db


def index_document(source_type: str, source_id: str, content: str, metadata: dict | None = None):
    chunks = _chunk_text(content)
    with get_db() as conn:
        for chunk in chunks:
            conn.execute(
                "INSERT INTO document_index (chunk_text, source_type, source_id, metadata) VALUES (?, ?, ?, ?)",
                (chunk, source_type, source_id, json.dumps(metadata or {})),
            )


def search_documents(query: str, source_type: str | None = None, limit: int = 5) -> list[dict]:
    keywords = _extract_keywords(query)
    if not keywords:
        return []

    with get_db() as conn:
        conditions = []
        params: list[Any] = []
        for kw in keywords:
            conditions.append("chunk_text LIKE ?")
            params.append(f"%{kw}%")
        sql = "SELECT * FROM document_index WHERE " + " OR ".join(conditions)
        if source_type:
            sql += " AND source_type = ?"
            params.append(source_type)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()

    results = []
    for row in rows:
        d = dict(row)
        try:
            d["metadata"] = json.loads(d.get("metadata", "{}"))
        except (json.JSONDecodeError, TypeError):
            d["metadata"] = {}
        results.append(d)
    return results


def index_log_content(log_id: int, events: list[dict]):
    content = "\n".join(
        f"[{e.get('line_number', '')}] {e.get('timestamp', '')} {e.get('source_ip', '')} {e.get('event_type', '')} {e.get('severity', '')}: {e.get('raw', '')}"
        for e in events
    )
    index_document("log", str(log_id), content, {"log_id": log_id, "event_count": len(events)})


def index_ioc_data(iocs: list[dict]):
    for ioc in iocs:
        content = f"IOC: {ioc['indicator']} Type: {ioc['indicator_type']} Score: {ioc.get('threat_score', 0)} Context: {ioc.get('context', '')}"
        index_document("ioc", ioc["indicator"], content, ioc)


def _chunk_text(text: str, max_chars: int = 1000) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    for i in range(0, len(text), max_chars):
        chunks.append(text[i:i + max_chars])
    return chunks


def _extract_keywords(text: str) -> list[str]:
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for",
                  "of", "by", "with", "from", "as", "be", "this", "that", "it", "what", "why",
                  "how", "which", "who", "where", "does", "did", "do", "has", "have", "had",
                  "not", "no", "but", "or", "and", "if", "so", "about", "can", "will", "would",
                  "could", "should", "may", "might", "please", "explain", "tell", "show", "me",
                  "the", "my", "its", "their", "our", "your", "his", "her"}
    words = re.findall(r"[a-zA-Z0-9.]+", text.lower())
    return [w for w in words if len(w) > 2 and w not in stop_words][:20]
