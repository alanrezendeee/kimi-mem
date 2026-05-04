"""Search and retrieval utilities for memories."""

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


def search_memories(query: str, project_path: str | None = None, limit: int = 10) -> list[dict]:
    """Search memories by query string."""
    return MemoryStore.search(query, project_path=project_path, limit=limit)


def get_recent_memories(project_path: str | None = None, limit: int = 10) -> list[dict]:
    """Get most recent memories."""
    return MemoryStore.recent(project_path=project_path, limit=limit)
