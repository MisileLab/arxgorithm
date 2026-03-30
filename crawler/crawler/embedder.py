"""Embedding generation via DeepInfra Qwen3-Embedding-0.6B API."""

import logging
import os
from typing import Iterator

from openai import OpenAI

logger = logging.getLogger(__name__)

_API_BASE_URL = "https://api.deepinfra.com/v1/openai"
_MODEL = "Qwen/Qwen3-Embedding-0.6B"
_MAX_BATCH = 64


def _get_client() -> OpenAI:
    """Return an OpenAI client pointed at the DeepInfra endpoint."""
    key = os.environ.get("DEEPINFRA_API_KEY", "")
    if not key:
        raise RuntimeError(
            "DEEPINFRA_API_KEY environment variable is not set. "
            "Export it before running the crawler."
        )
    return OpenAI(api_key=key, base_url=_API_BASE_URL)


def _call_api(texts: list[str]) -> list[list[float]]:
    """Call the DeepInfra embedding API and return embedding vectors.

    Args:
        texts: List of strings to embed (max 64 per call).

    Returns:
        List of embedding vectors (each a list of floats).

    Raises:
        RuntimeError: On unexpected API response shape.
    """
    client = _get_client()

    response = client.embeddings.create(
        model=_MODEL,
        input=texts,
    )

    # Sort by index to guarantee order matches input
    data = sorted(response.data, key=lambda item: item.index)
    return [item.embedding for item in data]


# ── Public API (signatures kept for backward compatibility) ──────────


def get_model(model_name: str | None = None):
    """No-op kept for backward compatibility.

    Previously initialised a local SentenceTransformer model.
    Now we call the DeepInfra API, so there is nothing to initialise.
    """
    return None


def generate_embedding(text: str, model_name: str | None = None) -> list[float]:
    """Generate a single embedding vector via DeepInfra API.

    Args:
        text: Combined title + abstract.
        model_name: Ignored (always uses DeepInfra Qwen3-Embedding-0.6B).

    Returns:
        List of floats (embedding vector).
    """
    logger.debug("Requesting embedding for text (%d chars)", len(text))
    results = _call_api([text])
    return results[0]


def generate_embeddings_batch(
    texts: list[str],
    model_name: str | None = None,
    batch_size: int = 64,
    show_progress: bool = True,
) -> list[list[float]]:
    """Generate embeddings for a batch of texts via DeepInfra API.

    Args:
        texts: List of title+abstract strings.
        model_name: Ignored (always uses DeepInfra Qwen3-Embedding-0.6B).
        batch_size: Max texts per API call (capped at 64).
        show_progress: Log progress info when True.

    Returns:
        List of embedding vectors.
    """
    batch_size = min(batch_size, _MAX_BATCH)
    logger.info(
        "Generating embeddings for %d texts via DeepInfra (batch_size=%d)",
        len(texts),
        batch_size,
    )

    all_embeddings: list[list[float]] = []
    chunks = list(chunk_texts(texts, batch_size))

    for idx, chunk in enumerate(chunks):
        if show_progress:
            logger.info("Processing chunk %d/%d (%d texts)", idx + 1, len(chunks), len(chunk))
        all_embeddings.extend(_call_api(chunk))

    return all_embeddings


def chunk_texts(texts: list[str], chunk_size: int = 64) -> Iterator[list[str]]:
    """Yield chunks of texts for memory-efficient batch processing."""
    for i in range(0, len(texts), chunk_size):
        yield texts[i : i + chunk_size]
