#!/usr/bin/env python3
"""Hook: SessionEnd / Stop — summarize session and store memories."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kimi_mem.db import init_db, SessionStore, ObservationStore, MemoryStore
from kimi_mem.summarizer import summarize_session
from kimi_mem.hooks.common import read_stdin, get_project_path, get_session_id


def main() -> None:
    init_db()
    data = read_stdin()

    session_id = get_session_id(data)
    project_path = get_project_path(data)
    _reason = data.get("reason", "")

    if not session_id:
        print("⚠️  No session ID found. Skipping summarization.", file=sys.stderr)
        return

    observations = ObservationStore.get_for_session(session_id)
    prompts = SessionStore.get_prompts(session_id)

    # If no observations, just end the session
    if not observations and not prompts:
        SessionStore.end(session_id, summary="No activity captured.")
        return

    # Build a richer context for summarization: include prompts + observations
    combined = []
    for p in prompts:
        combined.append({
            "type": "user_prompt",
            "content": p["prompt"],
            "created_at": p.get("created_at", ""),
        })
    for o in observations:
        combined.append({
            "type": o["type"],
            "tool_name": o.get("tool_name", ""),
            "content": o["content"],
            "created_at": o.get("created_at", ""),
        })

    # Sort by time
    combined.sort(key=lambda x: x.get("created_at", ""))

    # Generate AI summary
    result = summarize_session(combined)
    summary = result.get("summary", "")
    memories = result.get("memories", [])

    # Store extracted memories
    for mem in memories:
        MemoryStore.add(
            content=mem["content"],
            mem_type=mem.get("type", "pattern"),
            session_id=session_id,
            project_path=project_path,
            tags=mem.get("tags", []),
        )

    SessionStore.end(session_id, summary=summary, token_count=len(observations))
    print(f"✅ Session summarized: {summary[:100]}...", file=sys.stderr)
    print(f"🧠 Stored {len(memories)} memories.", file=sys.stderr)


if __name__ == "__main__":
    main()
