# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
