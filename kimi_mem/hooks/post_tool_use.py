#!/usr/bin/env python3
"""Hook: PostToolUse — capture tool usage observations."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kimi_mem.db import init_db, ObservationStore


def main() -> None:
    init_db()

    # Kimi hooks pass context via environment variables (documented in hooks beta)
    # If not available, we try to read from stdin or env
    tool_name = os.environ.get("KIMI_HOOK_TOOL_NAME", "unknown")
    tool_input = os.environ.get("KIMI_HOOK_TOOL_INPUT", "")
    tool_output = os.environ.get("KIMI_HOOK_TOOL_OUTPUT", "")
    session_id = os.environ.get("KIMI_MEM_SESSION_ID", "")

    if not session_id:
        # Try to read from a session file if available
        session_file = Path(".kimi") / ".kimi-mem-session"
        if session_file.exists():
            session_id = session_file.read_text().strip()

    if not session_id:
        return

    content = f"Tool: {tool_name}\nInput: {tool_input[:1000]}\nOutput: {tool_output[:2000]}"
    ObservationStore.add(
        session_id=session_id,
        obs_type="tool_use",
        content=content,
        tool_name=tool_name,
    )


if __name__ == "__main__":
    main()
