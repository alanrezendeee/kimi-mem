"""Generate text embeddings via Moonshot API or local fallback."""

import os

import httpx

MOONSHOT_API_BASE = os.environ.get("MOONSHOT_API_BASE", "https://api.moonshot.ai/v1")
EMBEDDING_MODEL = os.environ.get("KIMI_MEM_EMBEDDING_MODEL", "moonshot-v1-embedding")
EMBEDDING_DIM = int(os.environ.get("KIMI_MEM_EMBEDDING_DIM", "1024"))

# Simple local fallback: Bag-of-Characters hash embedding (deterministic, zero-deps)
# Not semantically meaningful but allows vector search to work without API key.
LOCAL_DIM = 384
TARGET_DIM = int(os.environ.get("KIMI_MEM_EMBEDDING_DIM", "1024"))


def _pad_embedding(vec: list[float], target_dim: int = TARGET_DIM) -> list[float]:
    """Pad or truncate vector to target dimension."""
    if len(vec) == target_dim:
        return vec
    if len(vec) < target_dim:
        return vec + [0.0] * (target_dim - len(vec))
    return vec[:target_dim]


def get_embedding(text: str, local_fallback: bool = True) -> list[float]:
    """Return embedding vector for text, padded to TARGET_DIM."""
    api_key = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("KIMI_API_KEY")
    if api_key:
        vec = _moonshot_embedding(text, api_key)
        return _pad_embedding(vec)
    if local_fallback:
        vec = _local_embedding(text)
        return _pad_embedding(vec)
    raise RuntimeError("No API key configured and local fallback disabled.")


def _moonshot_embedding(text: str, api_key: str) -> list[float]:
    try:
        response = httpx.post(
            f"{MOONSHOT_API_BASE}/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": EMBEDDING_MODEL, "input": text},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception as e:
        raise RuntimeError(f"Moonshot embedding failed: {e}")


def _local_embedding(text: str) -> list[float]:
    """Deterministic character-ngram hash embedding. Not semantic but structured."""
    vec = [0.0] * LOCAL_DIM
    text = text.lower()
    # Bigram hashing
    for i in range(len(text) - 1):
        bigram = text[i:i + 2]
        h = hash(bigram) % LOCAL_DIM
        vec[h] += 1.0
    # Normalize
    norm = sum(v * v for v in vec) ** 0.5
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec
