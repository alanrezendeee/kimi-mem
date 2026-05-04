"""Basic tests for kimi-mem database layer."""

import os
import tempfile

import pytest

from kimi_mem import db


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("KIMI_MEM_DB_PATH", os.path.join(tmpdir, "test.db"))
        db.init_db()
        yield


def test_add_and_search_memory():
    mid = db.MemoryStore.add("Test memory content", mem_type="note", tags=["test"])
    assert mid is not None
    results = db.MemoryStore.search("memory")
    assert len(results) == 1
    assert results[0]["content"] == "Test memory content"


def test_private_memory_excluded():
    db.MemoryStore.add("Secret <private>hidden</private> data", mem_type="note")
    public = db.MemoryStore.search("secret")
    private = db.MemoryStore.search("secret", include_private=True)
    assert len(public) == 0
    assert len(private) == 1


def test_observation_private_filtered():
    oid = db.ObservationStore.add("sess-1", "tool_use", "password = 123456", tool_name="Shell")
    assert oid is None
    oid2 = db.ObservationStore.add("sess-1", "tool_use", "echo hello", tool_name="Shell")
    assert oid2 is not None


def test_session_lifecycle():
    sid = db.SessionStore.start(project_path="/tmp/test")
    assert sid is not None
    db.SessionStore.end(sid, summary="Test session", token_count=42)
    with db.get_connection() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (sid,)).fetchone()
    assert row["summary"] == "Test session"
    assert row["token_count"] == 42
