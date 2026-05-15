#!/usr/bin/env python3
"""Debug hook: log everything Kimi CLI passes to hooks."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".kimi-mem" / "hook-debug.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def main():
    event = os.path.basename(__file__).replace(".py", "")
    if event == "debug":
        event = os.environ.get("KIMI_HOOK_EVENT", "unknown")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "cwd": os.getcwd(),
        "pid": os.getpid(),
        "args": sys.argv,
        "env": dict(os.environ),
    }

    # Read stdin if available
    if not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read()
            if stdin_data:
                entry["stdin"] = stdin_data
                # Try to parse as JSON
                try:
                    entry["stdin_json"] = json.loads(stdin_data)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            entry["stdin_error"] = str(e)
    else:
        entry["stdin"] = "<tty — no data>"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, indent=2, default=str))
        f.write("\n---\n")

    # Output something visible to the user
    print(f"[kimi-mem debug] {event} hook fired. Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
