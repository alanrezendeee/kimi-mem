"""Tests for kimi-mem MCP server tools."""

import asyncio
import os
import tempfile

import pytest

from kimi_mem import db
from kimi_mem.mcp_server import list_tools, call_tool


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("KIMI_MEM_DB_PATH", os.path.join(tmpdir, "test.db"))
        db.init_db()
        yield


def test_list_tools():
    tools = asyncio.run(list_tools())
    names = [t.name for t in tools]
    expected = [
        "kimi_mem_search",
        "kimi_mem_index",
        "kimi_mem_timeline",
        "kimi_mem_get",
        "kimi_mem_recent",
        "kimi_mem_add",
    ]
    assert names == expected


def test_kimi_mem_add():
    result = asyncio.run(call_tool("kimi_mem_add", {"content": "Test memory", "type": "note", "tags": ["test"]}))
    assert len(result) == 1
    assert "Added memory" in result[0].text


def test_kimi_mem_search():
    db.MemoryStore.add("Searchable content about Python", mem_type="pattern", tags=["python"])
    result = asyncio.run(call_tool("kimi_mem_search", {"query": "Python"}))
    assert len(result) == 1
    assert "Searchable content about Python" in result[0].text


def test_kimi_mem_index():
    db.MemoryStore.add("Indexed content", mem_type="note", tags=["test"])
    result = asyncio.run(call_tool("kimi_mem_index", {"query": "Indexed"}))
    assert len(result) == 1
    assert "Found" in result[0].text
    assert "Indexed content" in result[0].text


def test_kimi_mem_recent():
    db.MemoryStore.add("Recent memory", mem_type="note")
    result = asyncio.run(call_tool("kimi_mem_recent", {"limit": 5}))
    assert len(result) == 1
    assert "Recent memory" in result[0].text


def test_kimi_mem_get():
    mid = db.MemoryStore.add("Full detail memory", mem_type="decision", tags=["arch"])
    result = asyncio.run(call_tool("kimi_mem_get", {"memory_id": mid}))
    assert len(result) == 1
    assert "Full detail memory" in result[0].text
    assert "decision" in result[0].text


def test_kimi_mem_timeline():
    mid = db.MemoryStore.add("Timeline anchor", mem_type="note")
    result = asyncio.run(call_tool("kimi_mem_timeline", {"memory_id": mid, "window": 2}))
    assert len(result) == 1
    assert "Timeline around memory" in result[0].text


def test_unknown_tool():
    result = asyncio.run(call_tool("unknown_tool", {}))
    assert len(result) == 1
    assert "Unknown tool" in result[0].text
