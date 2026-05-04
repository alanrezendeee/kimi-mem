"""SQLite database layer with FTS5 full-text search."""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import sqlite_vec

from kimi_mem.config import get_db_path
from kimi_mem.embeddings import get_embedding

SCHEMA_SQL = """
-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    project_path TEXT,
    started_at TEXT,
    ended_at TEXT,
    summary TEXT,
    token_count INTEGER
);

-- Observations: individual tool uses, decisions, errors
CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    type TEXT NOT NULL,        -- 'tool_use', 'decision', 'error', 'note'
    tool_name TEXT,
    content TEXT NOT NULL,
    created_at TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Memories: compressed/summarized knowledge extracted from sessions
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    type TEXT NOT NULL,        -- 'pattern', 'decision', 'bugfix', 'architecture', 'config'
    content TEXT NOT NULL,
    project_path TEXT,
    tags TEXT,                 -- JSON list
    created_at TEXT,
    access_count INTEGER DEFAULT 0,
    last_accessed TEXT,
    is_private INTEGER DEFAULT 0
);

-- FTS5 virtual table for full-text search over memories
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    tags,
    content_rowid=rowid,
    content='memories'
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, content, tags)
    VALUES (new.rowid, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, tags)
    VALUES ('delete', old.rowid, old.content, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, tags)
    VALUES ('delete', old.rowid, old.content, old.tags);
    INSERT INTO memories_fts(rowid, content, tags)
    VALUES (new.rowid, new.content, new.tags);
END;

-- Virtual table for vector search (sqlite-vec)
CREATE VIRTUAL TABLE IF NOT EXISTS memory_vectors USING vec0(
    embedding float[{dim}]
);
""".format(dim=1024)


def get_connection() -> sqlite3.Connection:
    """Return a database connection with row factory."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    # Enable sqlite-vec extension
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)


class SessionStore:
    """Store and retrieve sessions."""

    @staticmethod
    def start(project_path: str | None = None) -> str:
        sid = str(uuid.uuid4())
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, project_path, started_at) VALUES (?, ?, ?)",
                (sid, project_path or "", datetime.now(timezone.utc).isoformat()),
            )
        return sid

    @staticmethod
    def end(session_id: str, summary: str | None = None, token_count: int = 0) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET ended_at = ?, summary = ?, token_count = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), summary or "", token_count, session_id),
            )


class ObservationStore:
    """Store raw observations from tool usage."""

    @staticmethod
    def add(
        session_id: str,
        obs_type: str,
        content: str,
        tool_name: str | None = None,
    ) -> str | None:
        from kimi_mem.privacy import is_private_observation
        if is_private_observation(content, tool_name):
            return None
        oid = str(uuid.uuid4())
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO observations (id, session_id, type, tool_name, content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (oid, session_id, obs_type, tool_name or "", content, datetime.now(timezone.utc).isoformat()),
            )
        return oid

    @staticmethod
    def get_for_session(session_id: str) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM observations WHERE session_id = ? ORDER BY created_at",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]


class MemoryStore:
    """Store compressed memories and search them."""

    @staticmethod
    def add(
        content: str,
        mem_type: str = "pattern",
        session_id: str | None = None,
        project_path: str | None = None,
        tags: list[str] | None = None,
        embedding: list[float] | None = None,
        is_private: bool = False,
    ) -> str:
        from kimi_mem.privacy import contains_private
        if contains_private(content):
            is_private = True
        mid = str(uuid.uuid4())
        if embedding is None and not is_private:
            try:
                embedding = get_embedding(content)
            except Exception:
                embedding = []

        with get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO memories (id, session_id, type, content, project_path, tags, created_at, is_private) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    mid,
                    session_id or "",
                    mem_type,
                    content,
                    project_path or "",
                    json.dumps(tags or []),
                    datetime.now(timezone.utc).isoformat(),
                    1 if is_private else 0,
                ),
            )
            if embedding and not is_private:
                conn.execute(
                    "INSERT INTO memory_vectors (rowid, embedding) VALUES (?, ?)",
                    (cur.lastrowid, json.dumps(embedding)),
                )
        return mid

    @staticmethod
    def search(query: str, project_path: str | None = None, limit: int = 10, semantic: bool = False, include_private: bool = False) -> list[dict]:
        """Full-text or semantic search over memories."""
        if semantic:
            return MemoryStore._semantic_search(query, project_path=project_path, limit=limit, include_private=include_private)

        sql = """
            SELECT m.* FROM memories m
            JOIN memories_fts fts ON m.rowid = fts.rowid
            WHERE memories_fts MATCH ? AND m.is_private = 0
        """
        if include_private:
            sql = """
                SELECT m.* FROM memories m
                JOIN memories_fts fts ON m.rowid = fts.rowid
                WHERE memories_fts MATCH ?
            """
        params: tuple = (query,)
        if project_path:
            sql += " AND m.project_path = ?"
            params += (project_path,)
        sql += " ORDER BY rank LIMIT ?"
        params += (limit,)

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def _semantic_search(query: str, project_path: str | None = None, limit: int = 10, include_private: bool = False) -> list[dict]:
        try:
            query_vec = get_embedding(query)
        except Exception:
            return []

        sql = """
            SELECT m.*, distance AS score
            FROM memories m
            JOIN memory_vectors v ON m.rowid = v.rowid
            WHERE v.embedding MATCH ? AND m.is_private = 0
            AND k = ?
        """
        if include_private:
            sql = """
                SELECT m.*, distance AS score
                FROM memories m
                JOIN memory_vectors v ON m.rowid = v.rowid
                WHERE v.embedding MATCH ?
                AND k = ?
            """
        params: tuple = (json.dumps(query_vec), limit)

        if project_path:
            sql += " AND m.project_path = ?"
            params += (project_path,)

        sql += " ORDER BY score"

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def recent(project_path: str | None = None, limit: int = 10, include_private: bool = False) -> list[dict]:
        sql = "SELECT * FROM memories WHERE is_private = 0"
        if include_private:
            sql = "SELECT * FROM memories WHERE 1=1"
        params: list = []
        if project_path:
            sql += " AND project_path = ?"
            params.append(project_path)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def get_by_id(memory_id: str) -> dict | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_timeline(memory_id: str, window: int = 2) -> list[dict]:
        """Get memories chronologically around a given memory."""
        with get_connection() as conn:
            target = conn.execute(
                "SELECT created_at FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
            if not target:
                return []

            rows = conn.execute(
                """
                SELECT * FROM memories
                WHERE created_at BETWEEN datetime(?, ?) AND datetime(?, ?)
                ORDER BY created_at
                """,
                (target["created_at"], f"-{window} hours", target["created_at"], f"+{window} hours"),
            ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def bump_access(memory_id: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), memory_id),
            )
