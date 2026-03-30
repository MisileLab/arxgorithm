"""pgvector similarity search service."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embedding import embed_text
from app.models.db_models import Paper

logger = logging.getLogger(__name__)


# ── Public API ─────────────────────────────────────────────────────────


def embed_query(text: str) -> list[float]:
    """Embed a query string using the configured embedding model."""
    return embed_text(text)


async def search_similar(
    embedding: list[float],
    *,
    limit: int = 10,
    category_filter: list[str] | None = None,
) -> list[tuple[Paper, float]]:
    """
    Search for papers with similar embeddings using pgvector.

    Creates its own database session. Returns a list of
    (Paper, similarity_score) tuples sorted by similarity desc.
    """
    from app.core.database import async_session_factory

    async with async_session_factory() as db:
        return await _do_search(db, embedding, limit=limit, category_filter=category_filter)


async def search_similar_with_db(
    embedding: list[float],
    db: AsyncSession,
    *,
    limit: int = 10,
    category_filter: list[str] | None = None,
) -> list[tuple[Paper, float]]:
    """
    Search for papers with similar embeddings using pgvector,
    using the provided *db* session.
    """
    return await _do_search(db, embedding, limit=limit, category_filter=category_filter)


async def index_paper(
    paper: Paper,
    embedding: list[float] | None = None,
    db: AsyncSession | None = None,
) -> bool:
    """Store a paper's embedding in the papers table via pgvector.

    If *db* is None, creates a short-lived session.
    """
    if embedding is None:
        text = f"{paper.title} {paper.abstract}"
        embedding = embed_text(text)

    own_session = db is None
    if own_session:
        from app.core.database import async_session_factory
        db = async_session_factory()

    try:
        stmt = (
            update(Paper)
            .where(Paper.arxiv_id == paper.arxiv_id)
            .values(embedding=embedding)
        )
        await db.execute(stmt)
        if own_session:
            await db.commit()
        return True
    except Exception as exc:
        logger.error("pgvector index failed for %s: %s", paper.arxiv_id, exc)
        if own_session:
            await db.rollback()
        return False
    finally:
        if own_session:
            await db.close()


# ── Internal helpers ───────────────────────────────────────────────────


async def _do_search(
    db: AsyncSession,
    embedding: list[float],
    *,
    limit: int = 10,
    category_filter: list[str] | None = None,
) -> list[tuple[Paper, float]]:
    """Execute a cosine-distance similarity search via pgvector."""
    try:
        # Build the query: compute cosine distance and order by it ascending
        # (lower distance = more similar). Convert to similarity score: 1 - distance.
        stmt = (
            select(
                Paper,
                (1 - Paper.embedding.cosine_distance(embedding)).label("score"),
            )
            .where(Paper.embedding.isnot(None))
        )

        # Apply category filter using JSON overlap (PostgreSQL && operator on arrays)
        if category_filter:
            # Filter papers whose categories array overlaps with the filter
            stmt = stmt.where(
                Paper.categories.bool_op("&&")(category_filter)
            )

        stmt = stmt.order_by(Paper.embedding.cosine_distance(embedding)).limit(limit)

        result = await db.execute(stmt)
        rows = result.all()

        return [(paper, float(score)) for paper, score in rows]

    except Exception as exc:
        logger.warning("pgvector search failed: %s – returning empty results", exc)
        return []
