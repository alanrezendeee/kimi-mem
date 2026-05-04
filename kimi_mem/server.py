"""Web viewer for kimi-mem — FastAPI dashboard."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from kimi_mem import __version__
from kimi_mem.db import get_connection, init_db
from kimi_mem.search import layer1_index, layer3_full

app = FastAPI(title="kimi-mem", version=__version__)


def _fmt_tags(tags_raw):
    tags_list = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw or []
    return ", ".join(tags_list)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧠 kimi-mem</title>
    <style>
        :root { --bg: #0d1117; --fg: #c9d1d9; --accent: #58a6ff; --muted: #8b949e; --card: #161b22; --border: #30363d; }
        * { box-sizing: border-box; }
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--fg); line-height: 1.5; }
        header { padding: 2rem; border-bottom: 1px solid var(--border); }
        header h1 { margin: 0; font-size: 1.75rem; }
        header p { margin: .25rem 0 0; color: var(--muted); }
        .container { max-width: 960px; margin: 0 auto; padding: 1.5rem; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
        .stat { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; text-align: center; }
        .stat .value { font-size: 1.5rem; font-weight: 600; color: var(--accent); }
        .stat .label { font-size: .875rem; color: var(--muted); margin-top: .25rem; }
        .search { display: flex; gap: .5rem; margin-bottom: 1.5rem; }
        .search input { flex: 1; padding: .6rem .8rem; border-radius: 6px; border: 1px solid var(--border); background: var(--card); color: var(--fg); font-size: 1rem; }
        .search button { padding: .6rem 1rem; border-radius: 6px; border: none; background: var(--accent); color: #fff; font-weight: 500; cursor: pointer; }
        .search label { display: flex; align-items: center; gap: .4rem; color: var(--muted); font-size: .9rem; }
        .memories { display: flex; flex-direction: column; gap: .75rem; }
        .memory { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; }
        .memory .meta { display: flex; gap: .5rem; align-items: center; margin-bottom: .5rem; flex-wrap: wrap; }
        .memory .badge { font-size: .7rem; text-transform: uppercase; padding: .15rem .4rem; border-radius: 4px; background: rgba(88,166,255,.15); color: var(--accent); font-weight: 600; }
        .memory .date { font-size: .8rem; color: var(--muted); }
        .memory .tags { font-size: .8rem; color: var(--muted); }
        .memory .content { white-space: pre-wrap; word-break: break-word; }
        .memory .score { font-size: .8rem; color: var(--muted); margin-left: auto; }
        .empty { text-align: center; color: var(--muted); padding: 2rem; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>🧠 kimi-mem</h1>
            <p>Persistent memory dashboard — v{{ version }}</p>
        </div>
    </header>
    <div class="container">
        <div class="stats">
            <div class="stat"><div class="value" id="stat-mem">-</div><div class="label">Memories</div></div>
            <div class="stat"><div class="value" id="stat-vec">-</div><div class="label">Vectors</div></div>
            <div class="stat"><div class="value" id="stat-obs">-</div><div class="label">Observations</div></div>
            <div class="stat"><div class="value" id="stat-sess">-</div><div class="label">Sessions</div></div>
        </div>
        <div class="search">
            <input type="text" id="q" placeholder="Search memories..." onkeydown="if(event.key==='Enter')search()">
            <button onclick="search()">Search</button>
            <label><input type="checkbox" id="semantic"> Semantic</label>
        </div>
        <div id="memories" class="memories"></div>
    </div>
    <script>
        async function loadStats() {
            const res = await fetch('/api/status');
            const data = await res.json();
            document.getElementById('stat-mem').textContent = data.memories;
            document.getElementById('stat-vec').textContent = data.vectors;
            document.getElementById('stat-obs').textContent = data.observations;
            document.getElementById('stat-sess').textContent = data.sessions;
        }
        async function search() {
            const q = document.getElementById('q').value;
            const semantic = document.getElementById('semantic').checked;
            const url = q ? `/api/memories?q=${encodeURIComponent(q)}&semantic=${semantic}` : '/api/memories';
            const res = await fetch(url);
            const data = await res.json();
            const container = document.getElementById('memories');
            if (!data.length) { container.innerHTML = '<div class="empty">No memories found.</div>'; return; }
            container.innerHTML = data.map(m => `
                <div class="memory">
                    <div class="meta">
                        <span class="badge">${m.type}</span>
                        <span class="date">${m.created_at}</span>
                        <span class="tags">${m.tags}</span>
                        ${m.score !== undefined ? `<span class="score">score: ${m.score.toFixed(3)}</span>` : ''}
                    </div>
                    <div class="content">${m.content}</div>
                </div>
            `).join('');
        }
        loadStats();
        search();
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_TEMPLATE.replace("{{ version }}", __version__)


@app.get("/api/status")
def api_status():
    init_db()
    with get_connection() as conn:
        mem = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        vec = conn.execute("SELECT COUNT(*) FROM memory_vectors").fetchone()[0]
        obs = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        sess = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    return {"memories": mem, "vectors": vec, "observations": obs, "sessions": sess, "version": __version__}


@app.get("/api/memories")
def api_memories(
    q: str | None = Query(None),
    semantic: bool = Query(False),
    limit: int = Query(50),
):
    init_db()
    if q:
        from kimi_mem.search import search_memories
        results = search_memories(q, limit=limit, semantic=semantic)
        for r in results:
            r["tags"] = _fmt_tags(r.get("tags", "[]"))
    else:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            results = [dict(r) for r in rows]
            for r in results:
                r["tags"] = _fmt_tags(r.get("tags", "[]"))
    return results


@app.get("/api/memories/{memory_id}")
def api_memory_detail(memory_id: str):
    init_db()
    mem = layer3_full(memory_id)
    if not mem:
        return {"error": "Not found"}
    mem["tags"] = _fmt_tags(mem.get("tags", "[]"))
    return mem
