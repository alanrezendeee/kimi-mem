#!/usr/bin/env python3
"""Hook: SessionStart — inject relevant memories into the session."""

import os
import sys
from pathlib import Path

# Allow running without package install
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kimi_mem.db import init_db, MemoryStore
from kimi_mem.search import format_for_injection


def main() -> None:
    init_db()
    project_path = os.environ.get("KIMI_MEM_PROJECT", os.getcwd())

    # Search for memories relevant to current project
    memories = MemoryStore.recent(project_path=project_path, limit=5)

    if not memories:
        # Fallback: search by project name as keyword
        project_name = Path(project_path).name
        memories = MemoryStore.search(project_name, project_path=None, limit=5)

    if not memories:
        return

    injection = format_for_injection(memories)

    # Write to a file that can be referenced by the agent
    mem_dir = Path(".kimi")
    mem_dir.mkdir(exist_ok=True)
    mem_file = mem_dir / "session-memory.md"
    mem_file.write_text(injection, encoding="utf-8")

    # Also print a concise summary for the hook output
    print(f"💾 Injected {len(memories)} memories into {mem_file}")
    for m in memories:
        print(f"  • [{m['type']}] {m['content'][:80]}...")


if __name__ == "__main__":
    main()
