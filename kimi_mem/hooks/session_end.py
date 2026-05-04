#!/usr/bin/env python3
"""Hook: SessionEnd / Stop — summarize session and store memories."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kimi_mem.db import init_db, SessionStore, ObservationStore, MemoryStore
from kimi_mem.summarizer import summarize_session


def main() -> None:
    init_db()
    session_id = os.environ.get("KIMI_MEM_SESSION_ID", "")
    project_path = os.environ.get("KIMI_MEM_PROJECT", os.getcwd())

    if not session_id:
        session_file = Path(".kimi") / ".kimi-mem-session"
        if session_file.exists():
            session_id = session_file.read_text().strip()
            session_file.unlink(missing_ok=True)

    if not session_id:
        print("⚠️  No session ID found. Skipping summarization.")
        return

    observations = ObservationStore.get_for_session(session_id)
    if not observations:
        SessionStore.end(session_id, summary="No observations captured.")
        return

    # Generate AI summary
    result = summarize_session(observations)
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
    print(f"✅ Session summarized: {summary[:100]}...")
    print(f"🧠 Stored {len(memories)} memories.")


if __name__ == "__main__":
    main()
