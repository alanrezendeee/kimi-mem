#!/usr/bin/env python3
"""Hook: Setup — verify kimi-mem installation health on Kimi CLI startup."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kimi_mem.config import get_db_path, get_kimi_config_path
from kimi_mem.hooks.common import write_output


def _check_python() -> tuple[bool, str]:
    """Verify the Python executable used by hooks still works."""
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return True, f"Python {result.stdout.strip()}"
        return False, f"Python exit code {result.returncode}"
    except Exception as e:
        return False, str(e)


def _check_db() -> tuple[bool, str]:
    """Verify SQLite DB is accessible and sqlite-vec loads."""
    db_path = get_db_path()
    if not db_path.exists():
        return True, f"DB not initialized yet ({db_path})"
    try:
        import sqlite_vec
        import sqlite3
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.execute("SELECT vec_version()")
        conn.close()
        return True, f"DB ok ({db_path.stat().st_size / 1024:.0f} KB)"
    except Exception as e:
        return False, str(e)


def _check_hooks_config() -> tuple[bool, str]:
    """Verify hooks are registered in Kimi config."""
    config_path = get_kimi_config_path()
    if not config_path:
        return False, "No Kimi config found"
    content = config_path.read_text(encoding="utf-8")
    if "kimi-mem hooks" not in content:
        return False, "kimi-mem hooks not found in config"
    events = ["SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "SessionEnd"]
    missing = [e for e in events if f'event = "{e}"' not in content]
    if missing:
        return False, f"Missing hooks: {', '.join(missing)}"
    return True, f"5 hooks found in {config_path}"


def _check_mcp() -> tuple[bool, str]:
    """Verify MCP server is registered."""
    mcp_file = Path.home() / ".kimi" / "mcp.json"
    if not mcp_file.exists():
        return True, "MCP not configured (optional)"
    try:
        data = json.loads(mcp_file.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", {})
        if "kimi-mem" in servers:
            return True, "kimi-mem MCP server registered"
        return True, "MCP config exists but kimi-mem not registered"
    except Exception as e:
        return False, str(e)


def main() -> None:
    checks = {
        "python": _check_python(),
        "database": _check_db(),
        "hooks": _check_hooks_config(),
        "mcp": _check_mcp(),
    }

    all_ok = all(ok for ok, _ in checks.values())
    messages = [f"  {'✅' if ok else '❌'} {name}: {msg}" for name, (ok, msg) in checks.items()]

    # Log to stderr so Kimi CLI doesn't parse it as hook output
    print("kimi-mem setup check:", file=sys.stderr)
    for m in messages:
        print(m, file=sys.stderr)

    if not all_ok:
        print("⚠️  kimi-mem has issues. Run: kimi-mem doctor", file=sys.stderr)

    # Return structured output for potential future Kimi CLI integration
    write_output({
        "hookSpecificOutput": {
            "hookEventName": "Setup",
            "kimi_mem_healthy": all_ok,
            "checks": {name: {"ok": ok, "message": msg} for name, (ok, msg) in checks.items()},
        }
    })


if __name__ == "__main__":
    main()
