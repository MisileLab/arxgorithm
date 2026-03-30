"""Embedding via DeepInfra OpenAI-compatible API (Qwen3-Embedding-0.6B)."""

import logging

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level OpenAI client pointed at DeepInfra (reused across calls)
_client = OpenAI(
    api_key=settings.deepinfra_api_key,
    base_url="https://api.deepinfra.com/v1/openai",
)


def _call_embedding_api(texts: list[str]) -> list[list[float]]:
    """Call the DeepInfra embeddings endpoint and return raw embedding vectors.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors (each a list of floats).

    Raises:
        RuntimeError: If the API call fails.
    """
    if not settings.deepinfra_api_key:
        raise RuntimeError(
            "DEEPINFRA_API_KEY is not configured. "
            "Set it in .env or as an environment variable."
        )

    try:
        response = _client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
        )
    except Exception as exc:
        logger.error("Embedding API request failed: %s", exc)
        raise RuntimeError(f"Embedding API request failed: {exc}") from exc

    # The OpenAI SDK returns data sorted by index by default, but we sort
    # explicitly to guarantee ordering matches input.
    data = sorted(response.data, key=lambda item: item.index)

    embeddings = [item.embedding for item in data]

    if len(embeddings) != len(texts):
        raise RuntimeError(
            f"Embedding API returned {len(embeddings)} results "
            f"for {len(texts)} inputs"
        )

    return embeddings


def embed_text(text: str) -> list[float]:
    """Embed a single string and return a list of floats.

    Drop-in replacement for the old sentence-transformers version.
    """
    results = _call_embedding_api([text])
    return results[0]


def embed_texts_batch(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings and return a list of float lists.

    Args:
        texts: List of strings to embed.

    Returns:
        List of embedding vectors.
    """
    if not texts:
        return []
    return _call_embedding_api(texts)
