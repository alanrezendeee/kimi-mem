"""Install kimi-mem hooks into Kimi CLI config.toml."""

import shutil
from pathlib import Path


from kimi_mem.config import get_kimi_config_path

HOOKS_CONFIG = """
# kimi-mem hooks — persistent memory for Kimi Code CLI
# Generated automatically. Safe to edit or remove.

[[hooks]]
event = "SessionStart"
command = "{python} -m kimi_mem.hooks.session_start"

[[hooks]]
event = "UserPromptSubmit"
command = "{python} -m kimi_mem.hooks.user_prompt_submit"

[[hooks]]
event = "PostToolUse"
command = "{python} -m kimi_mem.hooks.post_tool_use"

[[hooks]]
event = "Stop"
command = "{python} -m kimi_mem.hooks.session_end"

[[hooks]]
event = "SessionEnd"
command = "{python} -m kimi_mem.hooks.session_end"
"""


def get_python_executable() -> str:
    """Return the Python executable path."""
    return shutil.which("python3") or shutil.which("python") or "python3"


def install_hooks(dry_run: bool = False) -> None:
    """Append kimi-mem hooks to Kimi CLI config.toml."""
    config_path = get_kimi_config_path()
    if not config_path:
        # Create default config
        config_path = Path.home() / ".config" / "kimi" / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("", encoding="utf-8")
        print(f"Created new config at {config_path}")

    python = get_python_executable()
    hooks_block = HOOKS_CONFIG.format(python=python)

    content = config_path.read_text(encoding="utf-8")

    if "kimi-mem hooks" in content:
        print("⚠️  kimi-mem hooks already installed.")
        print(f"   Config: {config_path}")
        return

    if dry_run:
        print("--- Dry run: would append ---")
        print(hooks_block)
        return

    with open(config_path, "a", encoding="utf-8") as f:
        f.write("\n")
        f.write(hooks_block)

    print(f"✅ Installed kimi-mem hooks to {config_path}")
    print("🔄 Restart Kimi Code CLI for changes to take effect.")


def uninstall_hooks(dry_run: bool = False) -> None:
    """Remove kimi-mem hooks from Kimi CLI config.toml."""
    config_path = get_kimi_config_path()
    if not config_path:
        print("No Kimi config found.")
        return

    content = config_path.read_text(encoding="utf-8")
    if "kimi-mem hooks" not in content:
        print("No kimi-mem hooks found in config.")
        return

    lines = content.splitlines()
    filtered = []
    skip = False
    for line in lines:
        if "kimi-mem hooks" in line and "Generated automatically" in line:
            skip = True
            continue
        if skip and line.strip() and not line.strip().startswith("#") and not line.strip().startswith("["):
            continue
        if skip and line.strip().startswith("[["):
            skip = False
        if not skip:
            filtered.append(line)

    result = "\n".join(filtered).strip() + "\n"

    if dry_run:
        print("--- Dry run: would write ---")
        print(result)
        return

    config_path.write_text(result, encoding="utf-8")
    print(f"✅ Removed kimi-mem hooks from {config_path}")
