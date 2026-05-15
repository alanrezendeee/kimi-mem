# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.1] - 2026-05-15

### Added

- **Setup hook**: validates Python path, DB connectivity, sqlite-vec, hooks config, and MCP registration on Kimi CLI startup
- **`kimi-mem doctor` CLI command**: comprehensive health check for the entire installation
- **MCP server tests**: 8 new tests covering all 6 MCP tools (`kimi_mem_search`, `kimi_mem_index`, `kimi_mem_timeline`, `kimi_mem_get`, `kimi_mem_recent`, `kimi_mem_add`)
- **ROADMAP.md**: full audit report with feature parity matrix against claude-mem

### Fixed

- **`installer.py` uninstall**: never actually removed hooks because it looked for `"kimi-mem hooks"` and `"Generated automatically"` on the same line (they were on separate lines)
- **`installer.py` Python executable**: used system Python (`/opt/homebrew/bin/python3`) instead of the venv where kimi-mem is installed
- **`db.py` timeline query**: `MemoryStore.get_timeline()` failed to return results because it compared raw ISO 8601 timestamps with `datetime()` output in different string formats
- **`privacy.py`**: removed duplicate identical regex definitions (`PRIVATE_TAG_RE` and `PRIVATE_INDICATOR_RE`)
- **`embeddings.py`**: removed duplicate `TARGET_DIM` declaration
- **`session_start.py`**: added documentation comment about potential context double-injection (writes `session-memory.md` AND returns `additionalContext`)

## [0.2.0] - 2026-05-15

### Added

- **MCP Server**: 6 tools (`kimi_mem_search`, `kimi_mem_index`, `kimi_mem_timeline`, `kimi_mem_get`, `kimi_mem_recent`, `kimi_mem_add`) for auto-search by the agent
- `UserPromptSubmit` hook: captures user prompts and creates sessions idempotently
- `kimi-mem mcp-install` CLI command to register MCP server with Kimi CLI
- `kimi-mem mcp` CLI command to run the MCP server (stdio transport)
- `debug.py` hook for troubleshooting hook data from Kimi CLI
- `kimi_mem/hooks/common.py`: shared utilities for reading stdin JSON and writing structured output

### Changed

- **Complete hook rewrite** to use Kimi CLI's native stdin JSON format (discovered from `kimi_cli/hooks/runner.py` source)
- `SessionStart`: now creates sessions in DB and returns `additionalContext` via stdout JSON for native context injection
- `PostToolUse`: now reads real `tool_name`, `tool_input`, `tool_output` from stdin; filters low-value tools (Read, Shell, etc.)
- `SessionEnd/Stop`: now fetches observations + prompts and runs AI summarization end-to-end
- Database schema: added `user_prompts` table for storing user questions
- Privacy filter: improved regex heuristics to avoid false positives (e.g. `jsonwebtoken` no longer blocked)
- Version bump to 0.2.0

### Fixed

- Hooks no longer rely on non-existent environment variables (`KIMI_HOOK_TOOL_NAME`, etc.)
- Session ID now correctly persists across hooks using Kimi's native `session_id`
- Observations are now actually saved (was 0 before due to wrong input format)

## [0.1.4] - 2026-05-14

### Fixed

- `__init__.py`: align `__version__` with package version to prevent CLI `--version` mismatch

## [0.1.3] - 2026-05-14

### Fixed

- `session_start` hook: use absolute path (`~/.kimi/session-memory.md`) instead of relative path to avoid missing memory file on session restart
- `format_for_injection`: properly parse JSON-encoded tags from SQLite to prevent broken tag output in session memory

## [0.1.2] - 2026-05-04

### Fixed

- Escape FTS5 queries to prevent syntax errors with special characters (hyphens, quotes)

### Changed

- Added PATH note to README for venv/source installations

## [0.1.0] - 2026-05-04

### Added

- Initial release of kimi-mem
- SQLite persistent storage with FTS5 full-text search
- Native Kimi Code CLI hooks integration (SessionStart, PostToolUse, Stop, SessionEnd)
- AI-powered session summarization via Moonshot API
- Semantic vector search using sqlite-vec
- Progressive disclosure: 3-layer retrieval (index → timeline → full)
- Web viewer dashboard (FastAPI + HTML)
- Privacy tags: auto-exclude `<private>` content from search
- Manual memory management CLI (add, search, recent, status)
- Automatic hook installer/uninstaller
- MIT license
