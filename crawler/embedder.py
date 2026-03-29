"""Embedding generation for papers."""

import logging

logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector from text (title + abstract)."""
    # TODO: Implement with Sentence Transformers or OpenAI
    logger.info("Generating embedding...")
    return []
