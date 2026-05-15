#!/usr/bin/env python3
"""Hook: PostToolUse — capture tool usage observations."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kimi_mem.db import init_db, ObservationStore, SessionStore
from kimi_mem.privacy import strip_private
from kimi_mem.hooks.common import (
    read_stdin,
    get_project_path,
    get_session_id,
    is_skippable_tool,
)


def main() -> None:
    init_db()
    data = read_stdin()

    session_id = get_session_id(data)
    tool_name = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input", {})
    tool_output = data.get("tool_output", "")

    if not session_id:
        return

    # Skip low-value tools (same logic as claude-mem)
    if is_skippable_tool(tool_name):
        return

    # Ensure session exists (create if missing, for robustness)
    project_path = get_project_path(data)
    SessionStore.start_or_get(session_id, project_path=project_path)

    # Strip privacy tags from input/output
    input_str = json.dumps(tool_input) if isinstance(tool_input, dict) else str(tool_input)
    input_str = strip_private(input_str)
    output_str = strip_private(str(tool_output))

    content = f"Tool: {tool_name}\nInput: {input_str[:1000]}\nOutput: {output_str[:2000]}"

    ObservationStore.add(
        session_id=session_id,
        obs_type="tool_use",
        content=content,
        tool_name=tool_name,
    )


if __name__ == "__main__":
    main()
