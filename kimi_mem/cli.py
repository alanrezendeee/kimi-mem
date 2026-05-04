"""CLI entry point for kimi-mem."""

import json
import os
import sys
from pathlib import Path

import click

from kimi_mem import __version__
from kimi_mem.db import init_db, MemoryStore, ObservationStore, SessionStore
from kimi_mem.installer import install_hooks, uninstall_hooks
from kimi_mem.search import search_memories, get_recent_memories


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
def search(query: str, project: str | None, limit: int) -> None:
    """Search stored memories."""
    results = search_memories(query, project_path=project, limit=limit)
    if not results:
        click.echo("No memories found.")
        return
    for r in results:
        tags_raw = r.get("tags", "[]")
        tags_list = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw or []
        tags = ", ".join(tags_list)
        click.echo(f"\n[{r['type'].upper()}] {r['created_at']} | tags: {tags}")
        click.echo(f"  {r['content']}")


@main.command()
@click.option("--project", "-p", help="Filter by project path.")
@click.option("--limit", "-n", default=10, help="Max results.")
def recent(project: str | None, limit: int) -> None:
    """Show recent memories."""
    results = get_recent_memories(project_path=project, limit=limit)
    if not results:
        click.echo("No memories found.")
        return
    for r in results:
        tags_raw = r.get("tags", "[]")
        tags_list = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw or []
        tags = ", ".join(tags_list)
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
    click.echo(f"Memories: {mem_count} | Observations: {obs_count} | Sessions: {sess_count}")


@main.command()
def init() -> None:
    """Initialize the database."""
    init_db()
    click.echo("✅ Database initialized.")


if __name__ == "__main__":
    main()
