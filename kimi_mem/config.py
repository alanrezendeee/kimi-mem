"""Configuration and path management for kimi-mem."""

import os
from pathlib import Path

DEFAULT_DATA_DIR = Path.home() / ".kimi-mem"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "memory.db"
KIMI_CONFIG_PATH = Path.home() / ".config" / "kimi" / "config.toml"
KIMI_CONFIG_LEGACY = Path.home() / ".kimi" / "config.toml"

# Max tokens injected into session start to avoid bloating context
MAX_INJECTION_TOKENS = 2000
# Max memories retrieved per session start
MAX_MEMORIES_INJECT = 5


def get_data_dir() -> Path:
    """Return the data directory for kimi-mem."""
    path = Path(os.environ.get("KIMI_MEM_DATA_DIR", DEFAULT_DATA_DIR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_path() -> Path:
    """Return the SQLite database path."""
    return Path(os.environ.get("KIMI_MEM_DB_PATH", DEFAULT_DB_PATH))


def get_kimi_config_path() -> Path | None:
    """Locate the Kimi CLI config.toml."""
    for p in [KIMI_CONFIG_PATH, KIMI_CONFIG_LEGACY]:
        if p.exists():
            return p
    return None
