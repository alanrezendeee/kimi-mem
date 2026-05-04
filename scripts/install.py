#!/usr/bin/env python3
"""Standalone installer script for kimi-mem (no pip required)."""

import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.check_call(cmd)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    print("🔧 Installing kimi-mem...")
    print(f"   Source: {repo_root}")

    # Install package
    run([sys.executable, "-m", "pip", "install", "-e", str(repo_root)])

    # Install hooks
    run([sys.executable, "-m", "kimi_mem.cli", "install"])

    print("\n✅ kimi-mem installed!")
    print("🔄 Restart Kimi Code CLI to activate hooks.")
    print("\nNext steps:")
    print("  export KIMI_API_KEY='your-key'  # optional, for AI summaries")
    print("  kimi-mem status                 # check everything is working")


if __name__ == "__main__":
    main()
