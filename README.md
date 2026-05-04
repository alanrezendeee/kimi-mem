# 🧠 kimi-mem

> Persistent memory system for [Kimi Code CLI](https://github.com/MoonshotAI/kimi-cli).  
> Remember context across sessions. Never repeat yourself.

Inspired by [`claude-mem`](https://github.com/thedotmack/claude-mem), built for the Kimi ecosystem.

---

## ✨ Features

- 🔁 **Persistent Memory** — Context survives across Kimi sessions
- 🪝 **Native Hooks** — Uses Kimi CLI's built-in lifecycle hooks (Beta)
- 🔍 **Full-Text Search** — SQLite + FTS5 for fast memory retrieval
- 🤖 **AI Summarization** — Automatically compresses sessions into actionable memories via Moonshot API
- 🏷️ **Tagged & Typed** — Memories are categorized (pattern, decision, bugfix, architecture)
- 🌙 **Token-Efficient** — Injects only the most relevant memories, respects context limits
- ⚡ **Zero External Services** — SQLite is all you need; vector search optional

---

## 📦 Installation

### 1. Install the package

```bash
# Clone or download this repo
cd kimi-mem

# Install in editable mode (recommended for now)
pip install -e .

# Or install with vector search support
pip install -e ".[vector]"
```

### 2. Install hooks into Kimi CLI

```bash
kimi-mem install
```

This appends hook entries to your `~/.config/kimi/config.toml`.

> 🔄 **Restart Kimi Code CLI** for the hooks to take effect.

### 3. Set your API key (optional, for AI summarization)

```bash
export KIMI_API_KEY="your-moonshot-api-key"
```

If not set, kimi-mem still works — it just won't auto-summarize sessions with AI.

---

## 🚀 Quick Start

### Let it run automatically

Once installed, kimi-mem works in the background:

1. **Start a Kimi session** → relevant memories are injected into `.kimi/session-memory.md`
2. **Use tools (ReadFile, Shell, etc.)** → observations are captured silently
3. **End the session** → session is summarized and memories are stored

### Manual commands

```bash
# Search your memory
kimi-mem search "authentication bug"

# See recent memories
kimi-mem recent --limit 5

# Add a memory manually
kimi-mem add "Use jwt.ParseWithClaims for custom claims" \
  --type pattern --tag go --tag jwt

# Check status
kimi-mem status
```

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Kimi CLI   │────▶│   Hooks     │────▶│  kimi-mem core  │
│  (sessão)   │     │ (config.toml)│     │  (Python + SQLite)│
└─────────────┘     └─────────────┘     └─────────────────┘
                                                │
                       ┌────────────────────────┘
                       ▼
              ┌─────────────────┐
              │  SQLite + FTS5  │
              │  (memories +    │
              │   observations) │
              └─────────────────┘
```

### Hooks used

| Event | What it does |
|-------|-------------|
| `SessionStart` | Retrieves relevant memories → writes `.kimi/session-memory.md` |
| `PostToolUse` | Captures tool calls/outputs as observations |
| `Stop` / `SessionEnd` | Summarizes session with AI → stores compressed memories |

---

## ⚙️ Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `KIMI_API_KEY` | Moonshot API key for summarization | — |
| `KIMI_MEM_DATA_DIR` | Where to store the SQLite DB | `~/.kimi-mem` |
| `KIMI_MEM_DB_PATH` | Direct path to SQLite file | `~/.kimi-mem/memory.db` |
| `KIMI_MEM_MODEL` | Model for summarization | `moonshot-v1-8k` |
| `KIMI_MEM_PROJECT` | Override project path detection | `cwd` |

---

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

---

## 📋 Roadmap

- [x] SQLite + FTS5 full-text search
- [x] Native Kimi hooks integration
- [x] AI-powered session summarization
- [x] Manual memory management CLI
- [ ] **Vector embeddings** (`sqlite-vec` for semantic search)
- [ ] **Progressive disclosure** (3-layer retrieval like claude-mem)
- [ ] **Web viewer UI** (local HTTP dashboard)
- [ ] **Memory privacy tags** (`<private>` exclusion)
- [ ] **Cross-project memory linking**
- [ ] **PyPI publication** (`pip install kimi-mem`)

---

## 🤝 Contributing

This is an early alpha built by the community for the community.  
PRs, issues, and ideas are welcome!

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a PR

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

---

Built with 🌙 by [The Retech](https://github.com/theretech) and friends.
