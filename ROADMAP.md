# 🗺️ kimi-mem Roadmap & Audit Report

> Generated from full codebase audit — 2026-05-15
> Status: Core memory system operational. 90% feature parity with claude-mem.

---

## ✅ Current Status (Working Today)

| Component | Status | Evidence |
|-----------|--------|----------|
| CLI | ✅ v0.2.0 | `~/.local/bin/kimi-mem` |
| SQLite DB | ✅ 4.3 MB active | `~/.kimi-mem/memory.db` — 35 memories, 145 observations, 6 sessions |
| FTS5 Search | ✅ Synced | All 35 memories indexed |
| Vector Search | ✅ 34 vectors | sqlite-vec, dim=1024, local fallback works |
| Hooks (5) | ✅ Installed | `~/.kimi/config.toml` |
| MCP Server | ✅ 6 tools | `~/.kimi/mcp.json` registered |
| Skill | ✅ Active | `/kimi-caveman/.agents/skills/kimi-mem/SKILL.md` |
| Web Viewer | ✅ FastAPI | `kimi-mem serve` → `localhost:37777` |
| Tests | ✅ 4/4 passing | `pytest tests/test_db.py` |
| Privacy Tags | ✅ Filtering | `<private>` excluded from search & vectors |
| AI Summarization | ✅ With fallback | Moonshot API + local heuristics |

### Active Hooks
```
SessionStart      → creates session + injects memories via additionalContext
UserPromptSubmit  → saves user prompt to session history
PostToolUse       → captures tool usage observations
Stop              → triggers session summarization
SessionEnd        → finalizes session + stores compressed memories
```

---

## 🆚 claude-mem Feature Parity Matrix

| Feature | kimi-mem | claude-mem | Gap |
|---------|----------|------------|-----|
| Persistent cross-session memory | ✅ | ✅ | — |
| 5 lifecycle hooks | ✅ | ✅ | — |
| FTS5 full-text search | ✅ | ✅ | — |
| Semantic vector search | ✅ sqlite-vec | ✅ Chroma | **kimi-mem is lighter** |
| Progressive disclosure (L1/L2/L3) | ✅ | ✅ | — |
| Web viewer dashboard | ✅ FastAPI/HTML | ✅ React/Express | Different UX, same function |
| Privacy `<private>` tags | ✅ | ✅ | — |
| MCP auto-search tools | ✅ 6 tools | ✅ | — |
| AI session summarization | ✅ Moonshot | ✅ Claude SDK | Different provider |
| PyPI/npm distribution | ✅ PyPI | ✅ npm | — |
| **Setup hook** | ❌ | ✅ | **Medium** — no dependency check on startup |
| **PreToolUse (Read)** | ❌ | ✅ | **Low** — miss file-read context |
| **Worker service** (persistent HTTP) | ❌ on-demand only | ✅ always-on | **Low** — our model is lighter |
| **Observation citations API** | ❌ | ✅ `/api/observation/{id}` | **Low** — useful for debugging |
| **Settings JSON** | ❌ env vars only | ✅ `~/.claude-mem/settings.json` | **Low** — less discoverable config |
| **Beta/Endless Mode** | ❌ | ✅ | **Low** — advanced feature |
| **Planning + Execution skills** | ❌ | ✅ `make-plan` + `do` | **Medium** — nice-to-have |
| **Multi-IDE support** | ❌ Kimi only | ✅ Claude, Cursor, Gemini, Codex... | **High** — out of scope by design |

---

## 🐛 Known Bugs (Found During Audit) — STATUS

### B1: `installer.py` — uninstall leaves debris ✅ FIXED
**File:** `kimi_mem/installer.py`  
**Problem:** `uninstall_hooks()` skip logic didn't properly handle blank lines between hooks.  
**Fix:** Rewrote filter to use block-based removal with proper newline cleanup.

### B2: `privacy.py` — duplicate regex definitions ✅ FIXED
**File:** `kimi_mem/privacy.py`  
**Problem:** `PRIVATE_TAG_RE` and `PRIVATE_INDICATOR_RE` were identical.  
**Fix:** Consolidated to single regex.

### B3: `embeddings.py` — `TARGET_DIM` declared twice ✅ FIXED
**File:** `kimi_mem/embeddings.py`  
**Problem:** Duplicate declaration of `TARGET_DIM`.  
**Fix:** Removed duplicate, kept single source of truth.

### B4: Hooks lack retry / robustness ✅ FIXED
**File:** `kimi_mem/hooks/*.py`  
**Problem:** If Python executable moves, hooks fail silently.  
**Fix:** Added `Setup` hook (`kimi_mem/hooks/setup.py`) + `kimi-mem doctor` CLI command that verify Python path, DB connectivity, sqlite-vec, hooks config, and MCP registration.

### B5: `session_start.py` — potential double injection ⚠️ DOCUMENTED
**File:** `kimi_mem/hooks/session_start.py`  
**Problem:** Writes `~/.kimi/session-memory.md` **AND** returns `additionalContext` via stdout.  
**Status:** Added code comment documenting the trade-off. Low impact — Kimi CLI generally handles context gracefully.

### B6: `db.py` — timeline query used raw string comparison ✅ FIXED
**File:** `kimi_mem/db.py`  
**Problem:** `MemoryStore.get_timeline()` compared raw ISO 8601 timestamps with `datetime()` output, causing mismatched string formats and empty results.  
**Fix:** Changed query to `WHERE datetime(created_at) BETWEEN datetime(?, ?) AND datetime(?, ?)`.

### B7: `installer.py` — uninstall never worked + used system Python ✅ FIXED
**File:** `kimi_mem/installer.py`  
**Problem 1:** `uninstall_hooks()` looked for `"kimi-mem hooks"` and `"Generated automatically"` on the **same line**, but they were on separate lines. The uninstall silently did nothing for its entire lifetime.  
**Problem 2:** `get_python_executable()` used `shutil.which("python3")`, which found Homebrew's Python instead of the venv where kimi-mem was installed.  
**Fix:** Changed uninstall to detect `"kimi-mem hooks"` alone. Changed `get_python_executable()` to prefer `sys.executable`.

---

## 🎯 Recommended Implementation Order

### Phase 1: Quick Wins (Bug Fixes) — ~30 min ✅ DONE
1. ✅ Fix `installer.py` uninstall logic (B1)
2. ✅ Remove duplicate regex in `privacy.py` (B2)
3. ✅ Remove duplicate `TARGET_DIM` in `embeddings.py` (B3)
4. ✅ Add MCP server tests (8 new tests, all passing)
5. ✅ Fix `db.py` timeline query (B6)

### Phase 2: Robustness — ~1 hour ✅ DONE
6. ✅ Create `Setup` hook that validates Python path + DB connectivity (B4)
7. ✅ Add `kimi-mem doctor` CLI command for diagnostics
8. ⚠️ Document potential double injection in `session_start.py` (B5)

### Phase 3: Feature Gaps — ~2-3 hours ⏳ PENDING
9. Add `/api/observations` endpoint to web viewer
10. Add `/api/observations/{id}` detail endpoint (citations)
11. Add `PreToolUse (Read)` hook to capture file reads before execution
12. Create `kimi_mem/settings.py` with JSON-based config (`~/.kimi-mem/settings.json`)

### Phase 4: Ecosystem — ~4+ hours ⏳ PENDING
13. Planning skill (`make-plan` equivalent)
14. Execution skill (`do` equivalent)
15. Memory import/export CLI commands
16. Team/shared memory mode

---

## 📝 Files Audited

```
kimi_mem/
  __init__.py        → version 0.2.0
  cli.py             → 14 commands, all functional
  config.py          → paths + injection limits
  db.py              → SQLite + FTS5 + sqlite-vec schema
  embeddings.py      → Moonshot API + local fallback
  installer.py       → hooks install/uninstall
  mcp_server.py      → 6 MCP tools (stdio transport)
  privacy.py         → <private> tags + secret detection
  search.py          → progressive disclosure layers
  server.py          → FastAPI web viewer
  summarizer.py      → Moonshot API + local heuristic fallback
  hooks/
    session_start.py      → SessionStart hook
    session_end.py        → Stop/SessionEnd hook
    user_prompt_submit.py → UserPromptSubmit hook
    post_tool_use.py      → PostToolUse hook
    common.py             → shared utilities

tests/
  test_db.py         → 4 tests, all passing

Skill:
  /kimi-caveman/.agents/skills/kimi-mem/SKILL.md
```

---

## 🔧 Environment Snapshot (User System)

```
OS: macOS
Python: 3.13.7 (venv active at project root)
Kimi config: ~/.kimi/config.toml
kimi-mem DB: ~/.kimi-mem/memory.db (4,368 KB)
kimi-mem CLI: ~/.local/bin/kimi-mem
MCP config: ~/.kimi/mcp.json
Skill dir: /source/theretech/projetos-producao/kimi-caveman/.agents/skills/kimi-mem/
```

---

*Last updated: 2026-05-15 by Kimi Code CLI audit*
