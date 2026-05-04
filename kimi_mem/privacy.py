"""Privacy filtering for sensitive content."""

import re

PRIVATE_TAG_RE = re.compile(r"<private>.*?</private>", re.DOTALL | re.IGNORECASE)
PRIVATE_INDICATOR_RE = re.compile(r"<private>.*?</private>", re.DOTALL | re.IGNORECASE)


def contains_private(content: str) -> bool:
    """Check if content contains <private> tags."""
    if not content:
        return False
    return bool(PRIVATE_INDICATOR_RE.search(content))


def strip_private(content: str) -> str:
    """Remove <private>...</private> blocks from content."""
    if not content:
        return content
    return PRIVATE_TAG_RE.sub("[private content removed]", content)


def is_private_observation(content: str, tool_name: str | None = None) -> bool:
    """Determine if an observation should be excluded from storage."""
    if contains_private(content):
        return True
    # Also exclude common secret patterns
    lower = content.lower()
    secret_indicators = [
        "password", "secret", "api_key", "apikey", "token",
        "private_key", "ssh_key", "aws_secret", "credential",
    ]
    # Only trigger if combined with actual values (not just discussions)
    # Simple heuristic: contains '=' or ':' near the indicator
    if any(ind in lower for ind in secret_indicators):
        if "=" in content or ":" in content or "BEGIN" in content:
            return True
    return False
