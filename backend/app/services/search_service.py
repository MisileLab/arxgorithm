"""HelixDB vector search service."""

from __future__ import annotations

import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embedding import embed_text
from app.models.db_models import Paper

logger = logging.getLogger(__name__)

HELIXDB_COLLECTION = "papers"


# ── Public API ─────────────────────────────────────────────────────────


def embed_query(text: str) -> list[float]:
    """Embed a query string using the local sentence-transformers model."""
    return embed_text(text)


async def search_similar(
    embedding: list[float],
    *,
    limit: int = 10,
    category_filter: list[str] | None = None,
) -> list[tuple[Paper, float]]:
    """
    Search for papers with similar embeddings via HelixDB,
    then fetch the full Paper rows from PostgreSQL.

    Returns a list of (Paper, similarity_score) tuples sorted by score desc.
    """
    # Build HelixDB search payload
    payload: dict = {
        "collection": HELIXDB_COLLECTION,
        "vector": embedding,
        "limit": limit,
    }
    if category_filter:
        payload["filter"] = {
            "categories": {"$overlap": category_filter},
        }

    arxiv_ids_with_scores: list[tuple[str, float]] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.helixdb_url}/search",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            # HelixDB returns {"results": [{"id": ..., "score": ...}, ...]}
            results = data.get("results", data if isinstance(data, list) else [])
            for hit in results[:limit]:
                arxiv_id = hit.get("id") or hit.get("arxiv_id", "")
                score = float(hit.get("score", 0.0))
                if arxiv_id:
                    arxiv_ids_with_scores.append((arxiv_id, score))
    except httpx.HTTPError as exc:
        logger.warning("HelixDB search failed: %s – returning empty results", exc)
        return []

    if not arxiv_ids_with_scores:
        return []

    # Fetch matching Paper rows from Postgres
    ids_only = [aid for aid, _ in arxiv_ids_with_scores]
    score_map: dict[str, float] = dict(arxiv_ids_with_scores)

    # We need a db session – callers should pass one, or we create a short-lived one
    # For simplicity this function accepts an AsyncSession.
    # The router will supply it.
    return await _fetch_papers_by_arxiv_ids(ids_only, score_map, category_filter)


async def search_similar_with_db(
    embedding: list[float],
    db: AsyncSession,
    *,
    limit: int = 10,
    category_filter: list[str] | None = None,
) -> list[tuple[Paper, float]]:
    """
    Search for papers with similar embeddings via HelixDB,
    then fetch the full Paper rows from PostgreSQL using *db*.
    """
    payload: dict = {
        "collection": HELIXDB_COLLECTION,
        "vector": embedding,
        "limit": limit,
    }
    if category_filter:
        payload["filter"] = {
            "categories": {"$overlap": category_filter},
        }

    arxiv_ids_with_scores: list[tuple[str, float]] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.helixdb_url}/search",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", data if isinstance(data, list) else [])
            for hit in results[:limit]:
                arxiv_id = hit.get("id") or hit.get("arxiv_id", "")
                score = float(hit.get("score", 0.0))
                if arxiv_id:
                    arxiv_ids_with_scores.append((arxiv_id, score))
    except httpx.HTTPError as exc:
        logger.warning("HelixDB search failed: %s – returning empty results", exc)
        return []

    if not arxiv_ids_with_scores:
        return []

    ids_only = [aid for aid, _ in arxiv_ids_with_scores]
    score_map: dict[str, float] = dict(arxiv_ids_with_scores)

    stmt = select(Paper).where(Paper.arxiv_id.in_(ids_only))
    result = await db.execute(stmt)
    papers = result.scalars().all()

    # Preserve HelixDB ordering
    paper_by_id = {p.arxiv_id: p for p in papers}
    ordered: list[tuple[Paper, float]] = []
    for aid, score in arxiv_ids_with_scores:
        if aid in paper_by_id:
            ordered.append((paper_by_id[aid], score))

    return ordered


async def index_paper(paper: Paper, embedding: list[float] | None = None) -> bool:
    """Upsert a paper into HelixDB so it can be found via vector search."""
    if embedding is None:
        text = f"{paper.title} {paper.abstract}"
        embedding = embed_text(text)

    payload = {
        "collection": HELIXDB_COLLECTION,
        "id": paper.arxiv_id,
        "vector": embedding,
        "metadata": {
            "arxiv_id": paper.arxiv_id,
            "title": paper.title,
            "categories": paper.categories or [],
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.helixdb_url}/upsert",
                json=payload,
            )
            resp.raise_for_status()
            return True
    except httpx.HTTPError as exc:
        logger.error("HelixDB upsert failed for %s: %s", paper.arxiv_id, exc)
        return False


# ── Internal helpers ───────────────────────────────────────────────────


async def _fetch_papers_by_arxiv_ids(
    arxiv_ids: list[str],
    score_map: dict[str, float],
    category_filter: list[str] | None,
) -> list[tuple[Paper, float]]:
    """Fallback that creates its own session (used when no db passed)."""
    from app.core.database import async_session_factory

    async with async_session_factory() as db:
        stmt = select(Paper).where(Paper.arxiv_id.in_(arxiv_ids))
        result = await db.execute(stmt)
        papers = result.scalars().all()

        paper_by_id = {p.arxiv_id: p for p in papers}
        ordered: list[tuple[Paper, float]] = []
        for aid, score in arxiv_ids:
            if aid in paper_by_id:
                ordered.append((paper_by_id[aid], score))
        return ordered
