"""Singleton embedding model loader (sentence-transformers)."""

from functools import lru_cache

from app.core.config import settings


@lru_cache(maxsize=1)
def get_embedder():
    """Return a cached SentenceTransformer instance."""
    from sentence_transformers import SentenceTransformer  # heavy import

    return SentenceTransformer(settings.embedding_model_name)


def embed_text(text: str) -> list[float]:
    """Embed a single string and return a plain list of floats."""
    model = get_embedder()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()
