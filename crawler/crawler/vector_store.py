"""HelixDB vector storage client via REST API."""

import logging
from typing import Sequence

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

HELIXDB_DEFAULT_URL = "http://localhost:6334"
COLLECTION_NAME = "arxiv_papers"


class VectorStore:
    """Async HelixDB client for storing and searching paper embeddings."""

    def __init__(self, base_url: str = HELIXDB_DEFAULT_URL, timeout: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "VectorStore":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # ---- Collection management ----

    async def ensure_collection(self, vector_size: int = 384) -> None:
        """Create the papers collection if it doesn't exist."""
        client = await self._get_client()
        # Check if collection exists
        try:
            resp = await client.get(f"/collections/{COLLECTION_NAME}")
            if resp.status_code == 200:
                logger.info("Collection '%s' already exists", COLLECTION_NAME)
                return
        except httpx.HTTPStatusError:
            pass

        # Create collection with cosine distance
        resp = await client.put(
            f"/collections/{COLLECTION_NAME}",
            json={
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine",
                },
            },
        )
        resp.raise_for_status()
        logger.info("Created collection '%s' (dim=%d)", COLLECTION_NAME, vector_size)

    async def delete_collection(self) -> None:
        """Delete the papers collection."""
        client = await self._get_client()
        try:
            resp = await client.delete(f"/collections/{COLLECTION_NAME}")
            resp.raise_for_status()
            logger.info("Deleted collection '%s'", COLLECTION_NAME)
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                raise

    # ---- Vector operations ----

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def upsert_vectors(self, points: Sequence[dict]) -> None:
        """
        Upsert vector points into HelixDB.

        Each point should have:
          - id: string (arxiv_id)
          - vector: list[float]
          - payload: dict (metadata)
        """
        if not points:
            return

        client = await self._get_client()
        resp = await client.put(
            f"/collections/{COLLECTION_NAME}/points",
            json={"points": points},
        )
        resp.raise_for_status()
        logger.info("Upserted %d vectors into HelixDB", len(points))

    async def upsert_papers(
        self,
        paper_ids: Sequence[str],
        vectors: Sequence[list[float]],
        payloads: Sequence[dict],
    ) -> None:
        """
        Convenience method: upsert paper embeddings with metadata payloads.

        Args:
            paper_ids: arXiv paper IDs.
            vectors: Corresponding embedding vectors.
            payloads: Metadata dicts for each paper.
        """
        # Process in batches of 100 to avoid oversized requests
        batch_size = 100
        for i in range(0, len(paper_ids), batch_size):
            batch_ids = paper_ids[i : i + batch_size]
            batch_vectors = vectors[i : i + batch_size]
            batch_payloads = payloads[i : i + batch_size]

            points = [
                {
                    "id": pid,
                    "vector": vec,
                    "payload": payload,
                }
                for pid, vec, payload in zip(batch_ids, batch_vectors, batch_payloads)
            ]
            await self.upsert_vectors(points)

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
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
        Search for similar papers by embedding vector.

        Returns list of dicts with 'id', 'score', 'payload'.
        """
        client = await self._get_client()
        resp = await client.post(
            f"/collections/{COLLECTION_NAME}/search",
            json={
                "vector": query_vector,
                "limit": limit,
                "score_threshold": score_threshold,
                "with_payload": True,
            },
        )
        resp.raise_for_status()
        results = resp.json()
        return results if isinstance(results, list) else results.get("results", [])

    async def count_vectors(self) -> int:
        """Get the number of vectors in the collection."""
        client = await self._get_client()
        try:
            resp = await client.get(f"/collections/{COLLECTION_NAME}")
            resp.raise_for_status()
            info = resp.json()
            return info.get("vectors_count", info.get("points_count", 0))
        except httpx.HTTPStatusError:
            return 0
