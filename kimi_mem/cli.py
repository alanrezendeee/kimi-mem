"""CLI entry point for kimi-mem."""

import json
import os
import sys

import click

from kimi_mem import __version__
from kimi_mem.db import init_db, MemoryStore
from kimi_mem.installer import install_hooks, uninstall_hooks
from kimi_mem.search import (
    search_memories,
    get_recent_memories,
    layer1_index,
    layer2_timeline,
    layer3_full,
)


def _fmt_tags(tags_raw):
    tags_list = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw or []
    return ", ".join(tags_list)


@click.group()
@click.version_option(version=__version__, prog_name="kimi-mem")
def main() -> None:
    """kimi-mem: Persistent memory for Kimi Code CLI."""
    init_db()


@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would be done without changing files.")
def install(dry_run: bool) -> None:
    """Install kimi-mem hooks into Kimi CLI config."""
    install_hooks(dry_run=dry_run)


@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would be done without changing files.")
def uninstall(dry_run: bool) -> None:
    """Remove kimi-mem hooks from Kimi CLI config."""
    uninstall_hooks(dry_run=dry_run)


@main.command()
@click.argument("query")
@click.option("--project", "-p", help="Filter by project path.")
@click.option("--limit", "-n", default=10, help="Max results.")
@click.option("--semantic", "-s", is_flag=True, help="Use semantic (vector) search instead of full-text.")
@click.option("--include-private", is_flag=True, help="Include private memories in results.")
def search(query: str, project: str | None, limit: int, semantic: bool, include_private: bool) -> None:
    """Search stored memories (full-text or semantic)."""
    results = search_memories(query, project_path=project, limit=limit, semantic=semantic, include_private=include_private)
    if not results:
        click.echo("No memories found.")
        return
    for r in results:
        tags = _fmt_tags(r.get("tags", "[]"))
        score = f" | score: {r.get('score', 0):.3f}" if semantic else ""
        click.echo(f"\n[{r['type'].upper()}] {r['created_at']} | tags: {tags}{score}")
        click.echo(f"  {r['content']}")


@main.command()
@click.argument("query")
@click.option("--project", "-p", help="Filter by project path.")
@click.option("--limit", "-n", default=10, help="Max results.")
@click.option("--semantic", "-s", is_flag=True, help="Use semantic search.")
@click.option("--include-private", is_flag=True, help="Include private memories in results.")
def index(query: str, project: str | None, limit: int, semantic: bool, include_private: bool) -> None:
    """Progressive disclosure Layer 1: compact index (~50 tokens/result)."""
    results = layer1_index(query, project_path=project, limit=limit, semantic=semantic, include_private=include_private)
    if not results:
        click.echo("No memories found.")
        return
    click.echo(f"Found {len(results)} memories. Use 'timeline <id>' or 'get <id>' for details.\n")
    for r in results:
        tags = _fmt_tags(r.get("tags", "[]"))
        score = f" | score: {r.get('score', 0):.3f}" if semantic else ""
        click.echo(f"[{r['id'][:8]}] [{r['type'].upper()}] {r['created_at']}{score}")
        click.echo(f"  {r['preview']}")
        click.echo(f"  tags: {tags}\n")


@main.command("timeline")
@click.argument("memory_id")
@click.option("--window", "-w", default=2, help="Hours window around the memory.")
def timeline_cmd(memory_id: str, window: int) -> None:
    """Progressive disclosure Layer 2: chronological context around a memory."""
    results = layer2_timeline(memory_id, window=window)
    if not results:
        click.echo("Memory not found or no timeline available.")
        return
    click.echo(f"Timeline around memory (±{window}h):\n")
    for r in results:
        marker = " ⭐" if r["id"] == memory_id else ""
        tags = _fmt_tags(r.get("tags", "[]"))
        click.echo(f"[{r['created_at']}] [{r['type'].upper()}]{marker}")
        click.echo(f"  {r['content'][:200]}...")
        click.echo(f"  tags: {tags}\n")


@main.command("get")
@click.argument("memory_id")
def get_cmd(memory_id: str) -> None:
    """Progressive disclosure Layer 3: full memory detail."""
    mem = layer3_full(memory_id)
    if not mem:
        click.echo("Memory not found.")
        return
    tags = _fmt_tags(mem.get("tags", "[]"))
    click.echo(f"ID: {mem['id']}")
    click.echo(f"Type: {mem['type']}")
    click.echo(f"Created: {mem['created_at']}")
    click.echo(f"Project: {mem.get('project_path', 'n/a')}")
    click.echo(f"Tags: {tags}")
    click.echo(f"Access count: {mem.get('access_count', 0)}")
    click.echo(f"\n{mem['content']}")


@main.command()
@click.option("--project", "-p", help="Filter by project path.")
@click.option("--limit", "-n", default=10, help="Max results.")
@click.option("--include-private", is_flag=True, help="Include private memories in results.")
def recent(project: str | None, limit: int, include_private: bool) -> None:
    """Show recent memories."""
    results = get_recent_memories(project_path=project, limit=limit, include_private=include_private)
    if not results:
        click.echo("No memories found.")
        return
    for r in results:
        tags = _fmt_tags(r.get("tags", "[]"))
        click.echo(f"\n[{r['type'].upper()}] {r['created_at']} | tags: {tags}")
        click.echo(f"  {r['content']}")


@main.command()
@click.argument("content")
@click.option("--type", "-t", default="note", help="Memory type: pattern, decision, bugfix, architecture, note.")
@click.option("--project", "-p", default=lambda: os.getcwd(), help="Project path.")
@click.option("--tag", "-g", multiple=True, help="Tags to attach.")
def add(content: str, type: str, project: str, tag: tuple[str, ...]) -> None:
    """Manually add a memory."""
    mid = MemoryStore.add(
        content=content,
        mem_type=type,
        project_path=project,
        tags=list(tag),
    )
    click.echo(f"✅ Added memory {mid}")


@main.command()
def status() -> None:
    """Show kimi-mem status."""
    from kimi_mem.config import get_db_path, get_kimi_config_path
    db_path = get_db_path()
    config_path = get_kimi_config_path()

    click.echo(f"kimi-mem v{__version__}")
    click.echo(f"Database: {db_path} ({db_path.stat().st_size / 1024:.1f} KB)" if db_path.exists() else "Database: not initialized")
    click.echo(f"Kimi config: {config_path or 'not found'}")

    # Count records
    from kimi_mem.db import get_connection
    with get_connection() as conn:
        mem_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        obs_count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        sess_count = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        vec_count = conn.execute("SELECT COUNT(*) FROM memory_vectors").fetchone()[0]
    click.echo(f"Memories: {mem_count} | Vectors: {vec_count} | Observations: {obs_count} | Sessions: {sess_count}")


@main.command()
def init() -> None:
    """Initialize the database."""
    init_db()
    click.echo("✅ Database initialized.")


@main.command("serve")
@click.option("--host", default="127.0.0.1", help="Bind host.")
@click.option("--port", default=37777, help="Bind port.")
def serve(host: str, port: int) -> None:
    """Start the web viewer dashboard."""
    try:
        import uvicorn
        from kimi_mem.server import app
    except ImportError:
        click.echo("❌ Web dependencies not installed.")
        click.echo("   pip install 'kimi-mem[web]'")
        sys.exit(1)
    click.echo(f"🌐 Starting kimi-mem viewer at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
