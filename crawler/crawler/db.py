"""PostgreSQL storage for paper metadata via asyncpg."""

import logging
from typing import Sequence

import asyncpg

logger = logging.getLogger(__name__)

# DDL for the papers table
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS papers (
    arxiv_id      TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    abstract      TEXT NOT NULL DEFAULT '',
    authors       TEXT[] NOT NULL DEFAULT '{}',
    categories    TEXT[] NOT NULL DEFAULT '{}',
    published_at  TIMESTAMPTZ,
    updated_at    TIMESTAMPTZ,
    pdf_url       TEXT NOT NULL DEFAULT '',
    doi           TEXT NOT NULL DEFAULT '',
    journal_ref  TEXT NOT NULL DEFAULT '',
    comment       TEXT NOT NULL DEFAULT '',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_papers_published_at ON papers (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_papers_categories ON papers USING GIN (categories);
CREATE INDEX IF NOT EXISTS idx_papers_title_search ON papers USING GIN (to_tsvector('english', title));
"""


class PaperStore:
    """Async PostgreSQL store for paper metadata."""

    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create connection pool and ensure tables exist."""
        logger.info("Connecting to PostgreSQL: %s", self._dsn.split("@")[-1])
        self._pool = await asyncpg.create_pool(self._dsn, min_size=2, max_size=10)
        await self.ensure_schema()
        logger.info("PostgreSQL connected and schema ready")

    async def ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        async with self._pool.acquire() as conn:
            await conn.execute(_CREATE_TABLE_SQL)
            await conn.execute(_CREATE_INDEXES_SQL)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def __aenter__(self) -> "PaperStore":
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def upsert_paper(self, paper_dict: dict) -> None:
        """Insert or update a single paper."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO papers (arxiv_id, title, abstract, authors, categories,
                                    published_at, updated_at, pdf_url, doi, journal_ref, comment)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (arxiv_id) DO UPDATE SET
                    title        = EXCLUDED.title,
                    abstract     = EXCLUDED.abstract,
                    authors      = EXCLUDED.authors,
                    categories   = EXCLUDED.categories,
                    published_at = EXCLUDED.published_at,
                    updated_at   = EXCLUDED.updated_at,
                    pdf_url      = EXCLUDED.pdf_url,
                    doi          = EXCLUDED.doi,
                    journal_ref  = EXCLUDED.journal_ref,
                    comment      = EXCLUDED.comment
                """,
                paper_dict["arxiv_id"],
                paper_dict["title"],
                paper_dict.get("abstract", ""),
                paper_dict.get("authors", []),
                paper_dict.get("categories", []),
                paper_dict.get("published_at"),
                paper_dict.get("updated_at"),
                paper_dict.get("pdf_url", ""),
                paper_dict.get("doi", ""),
                paper_dict.get("journal_ref", ""),
                paper_dict.get("comment", ""),
            )

    async def upsert_papers_batch(self, papers: Sequence[dict]) -> int:
        """Bulk upsert papers using a transaction. Returns count of upserted papers."""
        if not papers:
            return 0
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(
                    """
                    INSERT INTO papers (arxiv_id, title, abstract, authors, categories,
                                        published_at, updated_at, pdf_url, doi, journal_ref, comment)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (arxiv_id) DO UPDATE SET
                        title        = EXCLUDED.title,
                        abstract     = EXCLUDED.abstract,
                        authors      = EXCLUDED.authors,
                        categories   = EXCLUDED.categories,
                        published_at = EXCLUDED.published_at,
                        updated_at   = EXCLUDED.updated_at,
                        pdf_url      = EXCLUDED.pdf_url,
                        doi          = EXCLUDED.doi,
                        journal_ref  = EXCLUDED.journal_ref,
                        comment      = EXCLUDED.comment
                    """,
                    [
                        (
                            p["arxiv_id"],
                            p["title"],
                            p.get("abstract", ""),
                            p.get("authors", []),
                            p.get("categories", []),
                            p.get("published_at"),
                            p.get("updated_at"),
                            p.get("pdf_url", ""),
                            p.get("doi", ""),
                            p.get("journal_ref", ""),
                            p.get("comment", ""),
                        )
                        for p in papers
                    ],
                )
        logger.info("Upserted %d papers into PostgreSQL", len(papers))
        return len(papers)

    async def get_paper(self, arxiv_id: str) -> dict | None:
        """Get a single paper by arXiv ID."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM papers WHERE arxiv_id = $1", arxiv_id
            )
        if row is None:
            return None
        return dict(row)

    async def get_unembedded_papers(self, limit: int = 100) -> list[dict]:
        """Get papers that don't have a corresponding vector in HelixDB yet.

        This is a heuristic — it checks for papers not in the recent
        embedding log. For now, just returns the most recent papers.
        """
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM papers
                ORDER BY published_at DESC
                LIMIT $1
                """,
                limit,
            )
        return [dict(r) for r in rows]

    async def count_papers(self) -> int:
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM papers")
