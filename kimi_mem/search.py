"""Search and retrieval utilities for memories — with progressive disclosure."""

from kimi_mem.db import MemoryStore
from kimi_mem.config import MAX_MEMORIES_INJECT, MAX_INJECTION_TOKENS


def format_for_injection(memories: list[dict]) -> str:
    """Format memories into a concise markdown block for context injection."""
    lines = ["# 💾 kimi-mem: Context from previous sessions\n"]
    total_tokens = 0

    for mem in memories[:MAX_MEMORIES_INJECT]:
        content = mem["content"].strip()
        # Rough token estimate: ~1.3 tokens per word
        estimated_tokens = len(content.split()) * 1.3
        if total_tokens + estimated_tokens > MAX_INJECTION_TOKENS:
            break

        tag_str = ", ".join(mem.get("tags", []) or [])
        lines.append(f"## [{mem['type'].upper()}] {tag_str}")
        lines.append(f"{content}\n")
        total_tokens += estimated_tokens

    return "\n".join(lines)


def search_memories(query: str, project_path: str | None = None, limit: int = 10, semantic: bool = False, include_private: bool = False) -> list[dict]:
    """Search memories by query string (text or semantic)."""
    return MemoryStore.search(query, project_path=project_path, limit=limit, semantic=semantic, include_private=include_private)


def get_recent_memories(project_path: str | None = None, limit: int = 10, include_private: bool = False) -> list[dict]:
    """Get most recent memories."""
    return MemoryStore.recent(project_path=project_path, limit=limit, include_private=include_private)


# Progressive Disclosure Layer 1: Compact Index

def layer1_index(query: str, project_path: str | None = None, limit: int = 10, semantic: bool = False, include_private: bool = False) -> list[dict]:
    """Return compact index with minimal fields (~50-100 tokens/result)."""
    results = MemoryStore.search(query, project_path=project_path, limit=limit, semantic=semantic, include_private=include_private)
    return [
        {
            "id": r["id"],
            "type": r["type"],
            "preview": r["content"][:120] + "..." if len(r["content"]) > 120 else r["content"],
            "created_at": r["created_at"],
            "tags": r.get("tags", []),
            "score": r.get("score", 0.0),
        }
        for r in results
    ]


# Progressive Disclosure Layer 2: Timeline Context

def layer2_timeline(memory_id: str, window: int = 2) -> list[dict]:
    """Get chronological context around a specific memory."""
    return MemoryStore.get_timeline(memory_id, window=window)


# Progressive Disclosure Layer 3: Full Detail

def layer3_full(memory_id: str) -> dict | None:
    """Fetch full observation details by ID."""
    return MemoryStore.get_by_id(memory_id)
