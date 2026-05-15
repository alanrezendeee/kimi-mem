#!/usr/bin/env python3
"""Hook: UserPromptSubmit — create session and save user prompt."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kimi_mem.db import init_db, SessionStore
from kimi_mem.privacy import strip_private
from kimi_mem.hooks.common import read_stdin, get_project_path, get_session_id


def main() -> None:
    init_db()
    data = read_stdin()

    session_id = get_session_id(data)
    project_path = get_project_path(data)
    prompt = data.get("prompt", "")

    if not session_id:
        return

    # Strip privacy tags from prompt
    cleaned_prompt = strip_private(prompt)
    if not cleaned_prompt or not cleaned_prompt.strip():
        # Fully private prompt — skip everything
        return

    # Create session if not exists (idempotent)
    SessionStore.start_or_get(session_id, project_path=project_path)

    # Save user prompt
    SessionStore.save_prompt(session_id, cleaned_prompt)


if __name__ == "__main__":
    main()
