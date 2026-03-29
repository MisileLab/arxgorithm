"""Embedding generation pipeline using sentence-transformers."""

import logging
from typing import Iterator

logger = logging.getLogger(__name__)

# Lazy-loaded model singleton
_model = None
_model_name: str = "all-MiniLM-L6-v2"


def get_model(model_name: str | None = None):
    """Get or initialize the sentence-transformers model (lazy load)."""
    global _model, _model_name
    if model_name:
        _model_name = model_name
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", _model_name)
        _model = SentenceTransformer(_model_name)
        logger.info(
            "Model loaded. Embedding dimension: %d", _model.get_sentence_embedding_dimension()
        )
    return _model


def generate_embedding(text: str, model_name: str | None = None) -> list[float]:
    """
    Generate a single embedding vector from text.

    Args:
        text: Combined title + abstract.
        model_name: Optional model override.

    Returns:
        List of floats (384-dim for all-MiniLM-L6-v2).
    """
    model = get_model(model_name)
    vector = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
    return vector.tolist()


def generate_embeddings_batch(
    texts: list[str],
    model_name: str | None = None,
    batch_size: int = 64,
    show_progress: bool = True,
) -> list[list[float]]:
    """
    Generate embeddings for a batch of texts efficiently.

    Args:
        texts: List of title+abstract strings.
        model_name: Optional model override.
        batch_size: Encoding batch size for GPU efficiency.
        show_progress: Show tqdm progress bar.

    Returns:
        List of embedding vectors.
    """
    model = get_model(model_name)
    logger.info("Generating embeddings for %d texts (batch_size=%d)", len(texts), batch_size)
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=show_progress,
    )
    return [v.tolist() for v in vectors]


def chunk_texts(texts: list[str], chunk_size: int = 64) -> Iterator[list[str]]:
    """Yield chunks of texts for memory-efficient batch processing."""
    for i in range(0, len(texts), chunk_size):
        yield texts[i : i + chunk_size]
