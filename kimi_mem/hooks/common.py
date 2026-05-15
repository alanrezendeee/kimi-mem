#!/usr/bin/env python3
"""Common utilities for Kimi CLI hooks."""

import json
import os
import sys
from pathlib import Path

# Tools to skip (low-value noise, same as claude-mem)
SKIP_TOOLS = {
    "ListMcpResourcesTool",
    "SlashCommand",
    "Skill",
    "TodoWrite",
    "AskUserQuestion",
}


def read_stdin() -> dict:
    """Read and parse JSON from stdin (how Kimi CLI passes hook data)."""
    try:
        raw = sys.stdin.read()
        if not raw:
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, Exception):
        return {}


def write_output(data: dict) -> None:
    """Write structured JSON output to stdout for Kimi CLI to parse.

    Kimi CLI parses stdout as JSON and looks for hookSpecificOutput key.
    SessionStart can return: {"hookSpecificOutput": {"additionalContext": "..."}}
    """
    print(json.dumps(data))
    sys.stdout.flush()


def get_project_path(data: dict) -> str:
    """Extract project path from hook payload."""
    return data.get("cwd", os.getcwd())


def get_session_id(data: dict) -> str:
    """Extract session_id from hook payload."""
    return data.get("session_id", "")


def is_skippable_tool(tool_name: str) -> bool:
    """Check if a tool should be skipped from observation capture."""
    return tool_name in SKIP_TOOLS
