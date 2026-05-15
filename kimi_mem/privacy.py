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

    # Exclude common secret patterns, but avoid false positives
    # on library names (e.g. "jsonwebtoken", "tokenizer", "csrf_token")
    lower = content.lower()
    secret_patterns = [
        r"password\s*[=:]\s*\S+",
        r"api[_-]?key\s*[=:]\s*\S+",
        r"secret\s*[=:]\s*\S+",
        r"private[_-]?key\s*[=:]\s*\S+",
        r"ssh[_-]?key\s*[=:]\s*\S+",
        r"aws[_-]?secret\s*[=:]\s*\S+",
        r"credential\s*[=:]\s*\S+",
        r"token\s*[=:]\s*[a-zA-Z0-9_\-]{10,}",  # token followed by actual value
        r"bearer\s+[a-zA-Z0-9_\-]{10,}",
        r"BEGIN\s+(RSA\s+)?PRIVATE\s+KEY",
    ]
    for pattern in secret_patterns:
        if re.search(pattern, lower):
            return True
    return False
