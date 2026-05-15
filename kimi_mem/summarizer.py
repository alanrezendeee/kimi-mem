"""Generate session summaries using the Moonshot AI API, with local fallback."""

import json
import os
import re

import httpx

MOONSHOT_API_BASE = os.environ.get("MOONSHOT_API_BASE", "https://api.moonshot.ai/v1")
DEFAULT_MODEL = os.environ.get("KIMI_MEM_MODEL", "moonshot-v1-8k")

SUMMARY_PROMPT = """You are a coding session summarizer. Your job is to extract persistent, actionable knowledge from a coding session.

Given a list of observations (tool uses, file edits, decisions, errors), produce a JSON object with this exact structure:
{
  "summary": "1-2 sentence overview of what was done",
  "memories": [
    {"type": "pattern", "content": "...", "tags": ["..."]},
    {"type": "decision", "content": "...", "tags": ["..."]},
    {"type": "bugfix", "content": "...", "tags": ["..."]},
    {"type": "architecture", "content": "...", "tags": ["..."]}
  ]
}

Rules:
- Only include memories that would be useful in FUTURE sessions (avoid temporary/debug stuff).
- "pattern": recurring code patterns, conventions, or best practices discovered.
- "decision": architectural or design decisions with reasoning.
- "bugfix": problems encountered and how they were solved.
- "architecture": structural changes, new modules, or refactoring notes.
- Tags should include relevant technologies (e.g., "go", "jwt", "docker", "testing").
- Keep each memory content under 200 words.
- If nothing worth remembering, return an empty memories array.

Observations:
{observations}
"""


def _local_summarize(observations: list[dict]) -> dict:
    """Fallback summarizer when AI API is unavailable. Extracts simple heuristics."""
    memories = []
    tech_tags = set()
    has_error = False
    has_fix = False
    tools_used = set()
    files_touched = set()
    prompts = []

    for obs in observations:
        content = obs.get("content", "")
        lower = content.lower()

        if obs.get("type") == "user_prompt":
            prompts.append(content)
            continue

        tool_name = obs.get("tool_name", "")
        if tool_name:
            tools_used.add(tool_name)

        # Extract file paths from tool inputs
        paths = re.findall(r'["\']([\w/.-]+\.[\w]+)["\']', content)
        files_touched.update(paths)

        # Detect tech tags
        tech_patterns = [
            (r"\b(jwt|auth|oauth|sso)\b", "auth"),
            (r"\b(docker|kubernetes|k8s)\b", "docker"),
            (r"\b(sqlite|postgres|mysql|mongodb|prisma)\b", "database"),
            (r"\b(react|vue|angular|svelte)\b", "frontend"),
            (r"\b(nestjs|express|fastapi|django|flask)\b", "backend"),
            (r"\b(typescript|javascript|python|go|rust|java)\b", "language"),
            (r"\b(test|jest|pytest|vitest|cypress)\b", "testing"),
            (r"\b(git|github|gitlab|ci/cd|github.actions)\b", "devops"),
        ]
        for pattern, tag in tech_patterns:
            if re.search(pattern, lower):
                tech_tags.add(tag)

        # Detect errors
        if "error" in lower or "exception" in lower or "fail" in lower:
            has_error = True
            if len(content) > 20:
                memories.append({
                    "type": "bugfix",
                    "content": f"Encountered issue during session: {content[:200]}...",
                    "tags": list(tech_tags) or ["session"],
                })

        # Detect fixes
        if any(w in lower for w in ["fix", "fixed", "resolve", "solved", "patch"]):
            has_fix = True
            if len(content) > 20:
                memories.append({
                    "type": "bugfix",
                    "content": f"Applied fix: {content[:200]}...",
                    "tags": list(tech_tags) or ["session"],
                })

    # Build summary
    parts = []
    if prompts:
        parts.append(f"Worked on: {prompts[0][:100]}...")
    if tools_used:
        parts.append(f"Tools used: {', '.join(sorted(tools_used))}.")
    if files_touched:
        parts.append(f"Files touched: {len(files_touched)}.")
    if has_error and has_fix:
        parts.append("Issues were encountered and resolved.")
    elif has_error:
        parts.append("Issues were encountered.")

    summary = " ".join(parts) if parts else "Session completed with no notable activity."

    # Deduplicate memories
    seen = set()
    unique_memories = []
    for m in memories:
        key = m["type"] + "|" + m["content"][:80]
        if key not in seen:
            seen.add(key)
            unique_memories.append(m)

    return {"summary": summary, "memories": unique_memories[:5]}


def summarize_session(observations: list[dict]) -> dict:
    """Call Moonshot API to summarize a session's observations. Falls back to local heuristics."""
    api_key = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY")
    if not api_key:
        return _local_summarize(observations)

    obs_text = "\n".join(
        f"[{o['type']}] {o.get('tool_name', '')}: {o['content'][:500]}"
        for o in observations
    )

    try:
        response = httpx.post(
            f"{MOONSHOT_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful coding assistant."},
                    {"role": "user", "content": SUMMARY_PROMPT.format(observations=obs_text)},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        # API failed (quota, network, etc.) — fall back to local summarizer
        return _local_summarize(observations)
