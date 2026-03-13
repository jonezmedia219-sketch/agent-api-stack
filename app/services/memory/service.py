import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models.memory import MemoryDeleteData, MemoryRecord, MemorySearchData, MemorySearchResult

_DEFAULT_DB_PATH = Path(".data") / "agent_memory.db"


class MemoryError(Exception):
    def __init__(self, *, code: str, message: str, status_code: int, retryable: bool = False):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        super().__init__(message)


def _get_db_path() -> Path:
    raw_path = os.getenv("MEMORY_DB_PATH")
    if raw_path:
        return Path(raw_path)
    return _DEFAULT_DB_PATH


def _get_connection() -> sqlite3.Connection:
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            memory_id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            scope TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_memories_agent_scope_created ON memories(agent_id, scope, created_at DESC)")
    connection.commit()


def _serialize_metadata(metadata: dict[str, Any]) -> str:
    return json.dumps(metadata, sort_keys=True)


def _deserialize_metadata(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise MemoryError(code="STORAGE_ERROR", message="Failed to load memory metadata.", status_code=500, retryable=False) from exc
    return parsed if isinstance(parsed, dict) else {}


def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
    return MemoryRecord(
        memory_id=row["memory_id"],
        agent_id=row["agent_id"],
        scope=row["scope"],
        content=row["content"],
        metadata=_deserialize_metadata(row["metadata_json"]),
        created_at=row["created_at"],
    )


def _tokenize(value: str) -> list[str]:
    return [token for token in "".join(ch.lower() if ch.isalnum() else " " for ch in value).split() if token]


def _score_memory(*, query: str, content: str, scope: str, metadata: dict[str, Any]) -> float:
    query_lc = query.lower().strip()
    if not query_lc:
        return 0.0

    corpus_parts = [content, scope, json.dumps(metadata, sort_keys=True)]
    corpus = " ".join(part.lower() for part in corpus_parts)
    query_tokens = _tokenize(query_lc)
    if not query_tokens:
        return 0.0

    token_hits = sum(1 for token in query_tokens if token in corpus)
    base_score = token_hits / len(query_tokens)
    if query_lc in corpus:
        base_score += 0.25
    if query_lc in content.lower():
        base_score += 0.15
    return round(min(base_score, 1.0), 2)


def store_memory(*, agent_id: str, scope: str, content: str, metadata: dict[str, Any]) -> MemoryRecord:
    memory_id = f"mem_{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(UTC).isoformat()
    try:
        with _get_connection() as connection:
            _ensure_table(connection)
            connection.execute(
                "INSERT INTO memories(memory_id, agent_id, scope, content, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (memory_id, agent_id, scope, content, _serialize_metadata(metadata), created_at),
            )
            connection.commit()
    except sqlite3.Error as exc:
        raise MemoryError(code="STORAGE_ERROR", message="Failed to store memory.", status_code=500, retryable=False) from exc

    return MemoryRecord(
        memory_id=memory_id,
        agent_id=agent_id,
        scope=scope,
        content=content,
        metadata=metadata,
        created_at=created_at,
    )


def search_memories(*, agent_id: str, query: str, limit: int, scope: str | None = None) -> MemorySearchData:
    try:
        with _get_connection() as connection:
            _ensure_table(connection)
            if scope:
                rows = connection.execute(
                    "SELECT memory_id, agent_id, scope, content, metadata_json, created_at FROM memories WHERE agent_id = ? AND scope = ? ORDER BY created_at DESC",
                    (agent_id, scope),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT memory_id, agent_id, scope, content, metadata_json, created_at FROM memories WHERE agent_id = ? ORDER BY created_at DESC",
                    (agent_id,),
                ).fetchall()
    except sqlite3.Error as exc:
        raise MemoryError(code="STORAGE_ERROR", message="Failed to search memories.", status_code=500, retryable=False) from exc

    scored: list[MemorySearchResult] = []
    for row in rows:
        metadata = _deserialize_metadata(row["metadata_json"])
        score = _score_memory(query=query, content=row["content"], scope=row["scope"], metadata=metadata)
        if score <= 0:
            continue
        scored.append(
            MemorySearchResult(
                memory_id=row["memory_id"],
                content=row["content"],
                scope=row["scope"],
                metadata=metadata,
                score=score,
                created_at=row["created_at"],
            )
        )

    scored.sort(key=lambda item: (item.score, item.created_at), reverse=True)
    return MemorySearchData(results=scored[:limit])


def delete_memory(*, memory_id: str) -> MemoryDeleteData:
    try:
        with _get_connection() as connection:
            _ensure_table(connection)
            cursor = connection.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
            connection.commit()
    except sqlite3.Error as exc:
        raise MemoryError(code="STORAGE_ERROR", message="Failed to delete memory.", status_code=500, retryable=False) from exc

    if cursor.rowcount == 0:
        raise MemoryError(code="NOT_FOUND", message="Memory not found.", status_code=404, retryable=False)

    return MemoryDeleteData(deleted=True, memory_id=memory_id)
