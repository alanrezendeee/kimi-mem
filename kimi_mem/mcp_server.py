#!/usr/bin/env python3
"""MCP server for kimi-mem — exposes memory search tools to Kimi CLI."""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from kimi_mem.db import init_db
from kimi_mem.search import (
    search_memories,
    get_recent_memories,
    layer1_index,
    layer2_timeline,
    layer3_full,
)

init_db()

app = Server("kimi-mem")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="kimi_mem_search",
            description="Search past memories by full-text or semantic query. Use when the user asks about previous work, decisions, bugs, patterns, or anything from past sessions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "project": {"type": "string", "description": "Filter by project path (optional)"},
                    "limit": {"type": "integer", "default": 10},
                    "semantic": {"type": "boolean", "default": False, "description": "Use semantic/vector search"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="kimi_mem_index",
            description="Progressive disclosure Layer 1: get compact index of memories (~50 tokens/result). Use first when searching to save tokens.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "semantic": {"type": "boolean", "default": False},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="kimi_mem_timeline",
            description="Progressive disclosure Layer 2: get chronological context around a memory ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                    "window": {"type": "integer", "default": 2, "description": "Hours around the memory"},
                },
                "required": ["memory_id"],
            },
        ),
        Tool(
            name="kimi_mem_get",
            description="Progressive disclosure Layer 3: get full details of a memory by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string"},
                },
                "required": ["memory_id"],
            },
        ),
        Tool(
            name="kimi_mem_recent",
            description="List recent memories. Use when user asks 'what did we do recently' or 'show last memories'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 5},
                },
            },
        ),
        Tool(
            name="kimi_mem_add",
            description="Manually add a memory. Use when user says 'remember this' or wants to save an insight.",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "type": {"type": "string", "enum": ["pattern", "decision", "bugfix", "architecture", "note"], "default": "note"},
                    "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                },
                "required": ["content"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    from kimi_mem.db import MemoryStore

    if name == "kimi_mem_search":
        results = search_memories(
            arguments["query"],
            project_path=arguments.get("project"),
            limit=arguments.get("limit", 10),
            semantic=arguments.get("semantic", False),
        )
        if not results:
            return [TextContent(type="text", text="No memories found.")]
        lines = []
        for r in results:
            tags = r.get("tags", "[]")
            if isinstance(tags, str):
                import json
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []
            score = f" | score: {r.get('score', 0):.3f}" if "score" in r else ""
            lines.append(f"[{r['type'].upper()}] {r['created_at']} | tags: {', '.join(tags)}{score}\n  {r['content']}")
        return [TextContent(type="text", text="\n\n".join(lines))]

    elif name == "kimi_mem_index":
        results = layer1_index(
            arguments["query"],
            limit=arguments.get("limit", 10),
            semantic=arguments.get("semantic", False),
        )
        if not results:
            return [TextContent(type="text", text="No memories found.")]
        lines = [f"Found {len(results)} memories. Use 'kimi_mem_timeline' or 'kimi_mem_get' for details.\n"]
        for r in results:
            tags = r.get("tags", "[]")
            if isinstance(tags, str):
                import json
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []
            score = f" | score: {r.get('score', 0):.3f}" if "score" in r else ""
            lines.append(f"[{r['id'][:8]}] [{r['type'].upper()}] {r['created_at']}{score}\n  {r['preview']}\n  tags: {', '.join(tags)}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "kimi_mem_timeline":
        results = layer2_timeline(arguments["memory_id"], window=arguments.get("window", 2))
        if not results:
            return [TextContent(type="text", text="Memory not found or no timeline available.")]
        lines = [f"Timeline around memory (±{arguments.get('window', 2)}h):\n"]
        for r in results:
            marker = " ⭐" if r["id"] == arguments["memory_id"] else ""
            tags = r.get("tags", "[]")
            if isinstance(tags, str):
                import json
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []
            lines.append(f"[{r['created_at']}] [{r['type'].upper()}]{marker}\n  {r['content'][:200]}...\n  tags: {', '.join(tags)}")
        return [TextContent(type="text", text="\n".join(lines))]

    elif name == "kimi_mem_get":
        mem = layer3_full(arguments["memory_id"])
        if not mem:
            return [TextContent(type="text", text="Memory not found.")]
        tags = mem.get("tags", "[]")
        if isinstance(tags, str):
            import json
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        text = (
            f"ID: {mem['id']}\n"
            f"Type: {mem['type']}\n"
            f"Created: {mem['created_at']}\n"
            f"Project: {mem.get('project_path', 'n/a')}\n"
            f"Tags: {', '.join(tags)}\n"
            f"Access count: {mem.get('access_count', 0)}\n\n"
            f"{mem['content']}"
        )
        return [TextContent(type="text", text=text)]

    elif name == "kimi_mem_recent":
        results = get_recent_memories(limit=arguments.get("limit", 5))
        if not results:
            return [TextContent(type="text", text="No memories found.")]
        lines = []
        for r in results:
            tags = r.get("tags", "[]")
            if isinstance(tags, str):
                import json
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []
            lines.append(f"[{r['type'].upper()}] {r['created_at']} | tags: {', '.join(tags)}\n  {r['content']}")
        return [TextContent(type="text", text="\n\n".join(lines))]

    elif name == "kimi_mem_add":
        mid = MemoryStore.add(
            content=arguments["content"],
            mem_type=arguments.get("type", "note"),
            tags=arguments.get("tags", []),
        )
        return [TextContent(type="text", text=f"✅ Added memory {mid}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
