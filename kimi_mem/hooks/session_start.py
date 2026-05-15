#!/usr/bin/env python3
"""Hook: SessionStart — create session and inject relevant memories into context."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kimi_mem.db import init_db, SessionStore, MemoryStore
from kimi_mem.search import format_for_injection
from kimi_mem.hooks.common import read_stdin, write_output, get_project_path, get_session_id


def main() -> None:
    init_db()
    data = read_stdin()

    session_id = get_session_id(data)
    project_path = get_project_path(data)
    _source = data.get("source", "startup")

    if not session_id:
        # Nothing we can do without a session id
        return

    # Create or get session (idempotent — same as claude-mem)
    SessionStore.start_or_get(session_id, project_path=project_path)

    # Retrieve relevant memories for this project
    memories = MemoryStore.recent(project_path=project_path, limit=5)
    if not memories:
        # Fallback: search by project name as keyword
        project_name = Path(project_path).name
        memories = MemoryStore.search(project_name, project_path=None, limit=5)

    if not memories:
        return

    injection = format_for_injection(memories)

    # Write to session-memory.md for the skill/agent to read
    mem_dir = Path.home() / ".kimi"
    mem_dir.mkdir(exist_ok=True)
    mem_file = mem_dir / "session-memory.md"
    mem_file.write_text(injection, encoding="utf-8")

    # Return structured context for Kimi CLI to inject directly
    # Kimi CLI parses stdout JSON and uses hookSpecificOutput.additionalContext
    write_output({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": injection,
        }
    })

    # Also print a concise summary for any logs
    print(f"💾 Injected {len(memories)} memories into context", file=sys.stderr)


if __name__ == "__main__":
    main()
