"""Generate session summaries using the Moonshot AI API."""

import json
import os

import httpx

MOONSHOT_API_BASE = os.environ.get("MOONSHOT_API_BASE", "https://api.moonshot.cn/v1")
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


def summarize_session(observations: list[dict]) -> dict:
    """Call Moonshot API to summarize a session's observations."""
    api_key = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY")
    if not api_key:
        return {"summary": "No API key configured.", "memories": []}

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
    except Exception as e:
        return {"summary": f"Summarization failed: {e}", "memories": []}
