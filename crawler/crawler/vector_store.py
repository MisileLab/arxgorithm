"""pgvector storage for paper embeddings via asyncpg."""

import logging
from typing import Sequence

import asyncpg
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from crawler.config import EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


class VectorStore:
    """Async PostgreSQL+pgvector client for storing and searching paper embeddings."""

    def __init__(self, dsn: str, embedding_dimension: int = EMBEDDING_DIMENSION):
        self._dsn = dsn
        self._embedding_dimension = embedding_dimension
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create connection pool and ensure the pgvector extension exists."""
        logger.info("Connecting to PostgreSQL (vector store): %s", self._dsn.split("@")[-1])
        self._pool = await asyncpg.create_pool(self._dsn, min_size=2, max_size=10)
        await self.ensure_extension()
        logger.info("PostgreSQL vector store connected and pgvector extension ready")

    async def ensure_extension(self) -> None:
        """Create the pgvector extension if it doesn't exist."""
        async with self._pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def __aenter__(self) -> "VectorStore":
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # ---- Vector operations ----

    @retry(
        retry=retry_if_exception_type((asyncpg.PostgresError, asyncpg.ConnectionDoesNotExistError, OSError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def upsert_vectors(self, points: Sequence[dict]) -> None:
        """
        Upsert vector embeddings into the papers table.

        Each point should have:
          - id: string (arxiv_id)
          - vector: list[float]
          - payload: dict (metadata, unused — stored in papers table already)
        """
        if not points:
            return

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for point in points:
                    arxiv_id = point["id"]
                    vector = point["vector"]
                    await conn.execute(
                        """
                        UPDATE papers
                        SET embedding = $2
                        WHERE arxiv_id = $1
                        """,
                        arxiv_id,
                        str(vector),  # asyncpg handles array-to-vector cast via string
                    )
        logger.info("Upserted %d vectors into pgvector", len(points))

    async def upsert_papers(
        self,
        paper_ids: Sequence[str],
        vectors: Sequence[list[float]],
        payloads: Sequence[dict],
    ) -> None:
        """
        Convenience method: upsert paper embeddings into the papers table.

        Args:
            paper_ids: arXiv paper IDs.
            vectors: Corresponding embedding vectors.
            payloads: Metadata dicts (ignored — metadata is already in the papers table).
        """
        # Process in batches of 100
        batch_size = 100
        for i in range(0, len(paper_ids), batch_size):
            batch_ids = paper_ids[i : i + batch_size]
            batch_vectors = vectors[i : i + batch_size]
            # payloads intentionally unused — metadata already stored in papers table

            points = [
                {"id": pid, "vector": vec}
                for pid, vec in zip(batch_ids, batch_vectors)
            ]
            await self.upsert_vectors(points)

    @retry(
        retry=retry_if_exception_type((asyncpg.PostgresError, asyncpg.ConnectionDoesNotExistError, OSError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        """
        Search for similar papers by embedding vector using cosine distance.

        Returns list of dicts with 'id', 'score', 'payload'.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT arxiv_id AS id,
                       1 - (embedding <=> $1::vector) AS score,
                       json_build_object(
                           'title', title,
                           'categories', categories,
                           'published_at', published_at
                       ) AS payload
                FROM papers
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                str(query_vector),
                limit,
            )

        results = []
        for row in rows:
            entry = dict(row)
            if entry.get("score", 0) >= score_threshold:
                results.append(entry)
        return results

    async def count_vectors(self) -> int:
        """Get the number of papers with embeddings stored."""
        async with self._pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL"
            )
            return count or 0

    async def ensure_collection(self, vector_size: int = EMBEDDING_DIMENSION) -> None:
        """No-op kept for API compatibility. pgvector doesn't use collections."""
        await self.ensure_extension()
        logger.info("pgvector extension ensured (dim=%d)", vector_size)

    async def delete_collection(self) -> None:
        """No-op kept for API compatibility."""
        logger.warning("delete_collection() is a no-op with pgvector")
