# 🧠 kimi-mem

> Persistent memory system for [Kimi Code CLI](https://github.com/MoonshotAI/kimi-cli).  
> Remember context across sessions. Never repeat yourself.

Inspired by [`claude-mem`](https://github.com/thedotmack/claude-mem), built for the Kimi ecosystem.

---

## ✨ Features

- 🔁 **Persistent Memory** — Context survives across Kimi sessions
- 🪝 **Native Hooks** — Uses Kimi CLI's built-in lifecycle hooks (Beta)
- 🔍 **Full-Text + Semantic Search** — SQLite FTS5 + sqlite-vec for hybrid retrieval
- 🎯 **Progressive Disclosure** — 3-layer retrieval: `index` → `timeline` → `get`
- 🤖 **AI Summarization** — Automatically compresses sessions into actionable memories via Moonshot API
- 🏷️ **Tagged & Typed** — Memories categorized as pattern, decision, bugfix, architecture
- 🔒 **Privacy Tags** — `<private>` blocks are automatically excluded from search/storage
- 🌐 **Web Viewer** — Local dashboard at `http://localhost:37777`
- 🌙 **Token-Efficient** — Injects only the most relevant memories, respects context limits
- ⚡ **Zero External Services** — SQLite is all you need; vector search included

---

## 📦 Installation

### 1. Install the package

```bash
pip install kimi-mem

# With web viewer support
pip install "kimi-mem[web]"
```

Or from source:

```bash
git clone https://github.com/theretech/kimi-mem.git
cd kimi-mem
pip install -e ".[web]"
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

### CLI Commands

```bash
# Search your memory (full-text)
kimi-mem search "authentication bug"

# Semantic search (vector)
kimi-mem search "how to handle jwt errors" --semantic

# Progressive disclosure
kimi-mem index "database migration"           # Layer 1: compact index
kimi-mem timeline <id>                        # Layer 2: chronological context
kimi-mem get <id>                             # Layer 3: full detail

# Recent memories
kimi-mem recent --limit 5

# Add a memory manually
kimi-mem add "Use jwt.ParseWithClaims for custom claims" \
  --type pattern --tag go --tag jwt

# Start web viewer
kimi-mem serve

# Check status
kimi-mem status
```

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Kimi CLI   │────▶│   Hooks     │────▶│  kimi-mem core  │
│  (session)  │     │ (config.toml)│     │  (Python + SQLite)│
└─────────────┘     └─────────────┘     └─────────────────┘
                                                │
                       ┌────────────────────────┘
                       ▼
              ┌─────────────────┐
              │  SQLite + FTS5  │
              │  + sqlite-vec   │
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

### Progressive Disclosure (3 layers)

Inspired by `claude-mem`, kimi-mem uses token-efficient layered retrieval:

| Layer | Command | Tokens | Purpose |
|-------|---------|--------|---------|
| L1 | `kimi-mem index <query>` | ~50-100/result | Compact preview with IDs |
| L2 | `kimi-mem timeline <id>` | ~200-500/result | Chronological context around a memory |
| L3 | `kimi-mem get <id>` | ~500-1000/result | Full content + metadata |

---

## 🔒 Privacy

kimi-mem respects your privacy:

- **`<private>...</private>`** tags in any content are automatically detected and excluded from search, vector index, and session injection
- Private memories are still stored (for your reference) but never retrieved automatically
- Heuristics detect secrets, passwords, and API keys in observations
- Use `--include-private` to explicitly search private memories

---

## ⚙️ Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `KIMI_API_KEY` | Moonshot API key for summarization | — |
| `KIMI_MEM_DATA_DIR` | Where to store the SQLite DB | `~/.kimi-mem` |
| `KIMI_MEM_DB_PATH` | Direct path to SQLite file | `~/.kimi-mem/memory.db` |
| `KIMI_MEM_MODEL` | Model for summarization | `moonshot-v1-8k` |
| `KIMI_MEM_EMBEDDING_MODEL` | Model for embeddings | `moonshot-v1-embedding` |
| `KIMI_MEM_EMBEDDING_DIM` | Embedding dimension | `1024` |

---

## 🛠️ Development

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,web]"

# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .
```

---

## 📋 Roadmap

- [x] SQLite + FTS5 persistent storage
- [x] Native Kimi CLI hooks
- [x] AI-powered session summarization
- [x] Semantic vector search (sqlite-vec)
- [x] Progressive disclosure (3-layer retrieval)
- [x] Web viewer dashboard
- [x] Privacy tags (`<private>` exclusion)
- [ ] PyPI publication
- [ ] Cross-project memory linking
- [ ] Memory import/export
- [ ] Team/shared memory

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
