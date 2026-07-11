"""RAG (Retrieval-Augmented Generation) service with FTS5 support."""
import json
import re
from typing import Optional

from src.database import get_db

STOP_WORDS: set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about", "up",
}


def index_document(source_type: str, source_id: str, content: str, metadata: Optional[dict] = None) -> None:
    chunks = _chunk_text(content)
    with get_db() as conn:
        for chunk in chunks:
            conn.execute(
                "INSERT INTO document_index (source_type, source_id, chunk_text, metadata) VALUES (?, ?, ?, ?)",
                (source_type, source_id, chunk, json.dumps(metadata or {})),
            )
        # Sync FTS index
        try:
            conn.execute("INSERT INTO document_fts(rowid, chunk_text, source_type) SELECT rowid, chunk_text, source_type FROM document_index WHERE rowid NOT IN (SELECT rowid FROM document_fts)")
        except Exception:
            pass


def search_documents(query: str, source_type: Optional[str] = None, limit: int = 10) -> list[dict]:
    keywords = _extract_keywords(query)
    if not keywords:
        return []

    with get_db() as conn:
        # Try FTS5 search first
        try:
            fts_query = " AND ".join(keywords)
            sql = """
                SELECT d.*, rank FROM document_fts f
                JOIN document_index d ON d.rowid = f.rowid
                WHERE document_fts MATCH ?
            """
            params: list[str] = [fts_query]
            if source_type:
                sql += " AND f.source_type = ?"
                params.append(source_type)
            sql += " ORDER BY rank LIMIT ?"
            params.append(str(limit))
            rows = conn.execute(sql, params).fetchall()
        except Exception:
            # Fallback to LIKE search if FTS fails
            conditions = " OR ".join(["d.chunk_text LIKE ?"] * len(keywords))
            params = [f"%{kw}%" for kw in keywords]
            sql = f"SELECT d.* FROM document_index d WHERE {conditions}"
            if source_type:
                sql += " AND d.source_type = ?"
                params.append(source_type)
            sql += " ORDER BY d.created_at DESC LIMIT ?"
            params.append(str(limit))
            rows = conn.execute(sql, params).fetchall()

    results = []
    for r in rows:
        item = dict(r)
        try:
            item["metadata"] = json.loads(item.get("metadata", "{}"))
        except (json.JSONDecodeError, TypeError):
            item["metadata"] = {}
        results.append(item)
    return results


def index_log_content(log_id: int, events: list[dict]) -> None:
    text = "\n".join(
        f"[{e.get('timestamp', '')}] {e.get('source_ip', '')} {e.get('event_type', '')} {e.get('severity', '')}: {e.get('raw', '')}"
        for e in events
    )
    index_document("log", str(log_id), text, {"event_count": len(events)})


def index_ioc_data(iocs: list[dict]) -> None:
    for ioc in iocs:
        text = f"{ioc.get('ioc_type', 'unknown')}: {ioc.get('indicator', '')} - {ioc.get('description', '')}"
        index_document("ioc", ioc.get("indicator", str(id(ioc))), text, ioc)


def _chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    """Split text into word-aligned chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= chunk_size:
            chunks.append(text)
            break

        # Find last space within chunk_size
        split_at = text.rfind(" ", 0, chunk_size)
        if split_at == -1:
            split_at = chunk_size

        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()

    return chunks


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from query text."""
    words = re.findall(r"[A-Za-z0-9_\-.]+", text.lower())
    keywords = [w for w in words if len(w) > 2 and w not in STOP_WORDS]
    return keywords[:10]
