"""arXgorithm crawler — CLI entry point.

Usage:
    crawl search --query "cat:cs.AI" --max 100
    crawl bulk --path /data/arxiv-dump.xml
    crawl embed --model all-MiniLM-L6-v2
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone

import click

from crawler.config import (
    DATABASE_URL,
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIMENSION,
    LOG_LEVEL,
)

logger = logging.getLogger("crawler")


def setup_logging(level: str = LOG_LEVEL) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )


# ─── CLI Group ───────────────────────────────────────────────────────────────


@click.group()
@click.option("--log-level", default=LOG_LEVEL, help="Log level (DEBUG, INFO, WARNING, ERROR)")
def cli(log_level: str) -> None:
    """arXgorithm crawler — fetch arXiv papers, generate embeddings, store vectors."""
    setup_logging(log_level)


# ─── search ──────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--query", "-q", required=True, help='arXiv search query (e.g. "cat:cs.AI", "ti:transformer")')
@click.option("--max", "max_results", default=100, help="Maximum papers to fetch")
@click.option("--sort-by", default="submittedDate", help="Sort field (submittedDate, relevance, lastUpdatedDate)")
@click.option("--sort-order", default="descending", help="Sort order (ascending, descending)")
@click.option("--store/--no-store", default=True, help="Store results in DB and vector store")
@click.option("--embed/--no-embed", default=True, help="Generate embeddings")
@click.option("--output", "-o", default=None, help="Output JSON file path")
def search(
    query: str,
    max_results: int,
    sort_by: str,
    sort_order: str,
    store: bool,
    embed: bool,
    output: str | None,
) -> None:
    """Search arXiv API and process papers."""
    asyncio.run(_search(query, max_results, sort_by, sort_order, store, embed, output))


async def _search(
    query: str,
    max_results: int,
    sort_by: str,
    sort_order: str,
    store: bool,
    embed: bool,
    output: str | None,
) -> None:
    from crawler.arxiv_client import ArxivClient
    from crawler.embedder import generate_embedding, generate_embeddings_batch

    all_papers = []

    async with ArxivClient() as client:
        async for batch in client.search(query, max_results, sort_by, sort_order):
            logger.info("Received batch of %d papers", len(batch))
            all_papers.extend(batch)

    if not all_papers:
        logger.warning("No papers found for query: %s", query)
        return

    logger.info("Total papers fetched: %d", len(all_papers))

    # Generate embeddings
    if embed:
        texts = [p.embedding_text for p in all_papers]
        logger.info("Generating embeddings for %d papers...", len(texts))
        vectors = generate_embeddings_batch(texts, show_progress=True)
        logger.info("Embeddings generated (dim=%d)", len(vectors[0]) if vectors else 0)
    else:
        vectors = []

    # Store in DB and vector store
    if store:
        await _store_papers(all_papers, vectors if embed else [])

    # Output to file
    if output:
        data = []
        for i, p in enumerate(all_papers):
            entry = p.to_dict()
            if embed and i < len(vectors):
                entry["embedding"] = vectors[i]
            data.append(entry)
        with open(output, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("Wrote %d papers to %s", len(data), output)
    else:
        # Print summary to stdout
        for p in all_papers[:20]:
            click.echo(f"  {p.arxiv_id}  {p.title[:80]}")
        if len(all_papers) > 20:
            click.echo(f"  ... and {len(all_papers) - 20} more")


# ─── bulk ────────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--path", "-p", required=True, help="Path to arXiv bulk dump XML file")
@click.option("--embed/--no-embed", default=True, help="Generate embeddings")
@click.option("--store/--no-store", default=True, help="Store in DB and vector store")
@click.option("--batch-size", default=500, help="Number of papers per processing batch")
def bulk(path: str, embed: bool, store: bool, batch_size: int) -> None:
    """Process an arXiv bulk dump file."""
    asyncio.run(_bulk(path, embed, store, batch_size))


async def _bulk(path: str, embed: bool, store: bool, batch_size: int) -> None:
    from crawler.arxiv_client import parse_bulk_dump_file
    from crawler.embedder import generate_embeddings_batch

    logger.info("Parsing bulk dump file: %s", path)
    papers = parse_bulk_dump_file(path)
    logger.info("Parsed %d papers from bulk dump", len(papers))

    if not papers:
        logger.warning("No papers found in dump file")
        return

    # Process in batches
    total_stored = 0
    for i in range(0, len(papers), batch_size):
        batch = papers[i : i + batch_size]
        vectors = []
        if embed:
            texts = [p.embedding_text for p in batch]
            vectors = generate_embeddings_batch(texts, show_progress=True)

        if store:
            await _store_papers(batch, vectors)

        total_stored += len(batch)
        logger.info(
            "Progress: %d / %d papers processed", total_stored, len(papers)
        )

    logger.info("Bulk processing complete: %d papers", total_stored)


# ─── embed ───────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--model", "-m", default=DEFAULT_EMBEDDING_MODEL, help="Sentence-transformers model name")
@click.option("--limit", default=100, help="Max papers to embed (0 = all)")
@click.option("--re-embed/--no-re-embed", default=False, help="Re-embed papers that already have vectors")
def embed(model: str, limit: int, re_embed: bool) -> None:
    """Generate embeddings for papers already stored in PostgreSQL."""
    asyncio.run(_embed(model, limit, re_embed))


async def _embed(model: str, limit: int, re_embed: bool) -> None:
    from crawler.db import PaperStore
    from crawler.embedder import generate_embedding, generate_embeddings_batch
    from crawler.vector_store import VectorStore

    logger.info("Embedding papers with model: %s", model)

    async with PaperStore(DATABASE_URL) as store:
        if re_embed:
            papers = await store.get_unembedded_papers(limit=limit if limit > 0 else 10000)
        else:
            papers = await store.get_papers_without_embeddings(limit=limit if limit > 0 else 10000)

    if not papers:
        logger.info("No papers to embed")
        return

    logger.info("Found %d papers to embed", len(papers))

    texts = [
        f"{p['title']}\n\n{p.get('abstract', '')}" for p in papers
    ]
    vectors = generate_embeddings_batch(texts, model_name=model, show_progress=True)

    # Build payloads (metadata already in papers table, but keep for API compat)
    ids = [p["arxiv_id"] for p in papers]
    payloads = [
        {
            "title": p["title"],
            "categories": p.get("categories", []),
            "published_at": str(p.get("published_at", "")),
        }
        for p in papers
    ]

    async with VectorStore(DATABASE_URL) as vs:
        await vs.ensure_collection(vector_size=len(vectors[0]) if vectors else EMBEDDING_DIMENSION)
        await vs.upsert_papers(ids, vectors, payloads)

    logger.info("Embedded and stored %d vectors", len(vectors))


# ─── stats ───────────────────────────────────────────────────────────────────


@cli.command()
def stats() -> None:
    """Show crawler statistics (paper count, vector count)."""
    asyncio.run(_stats())


async def _stats() -> None:
    from crawler.db import PaperStore
    from crawler.vector_store import VectorStore

    try:
        async with PaperStore(DATABASE_URL) as store:
            paper_count = await store.count_papers()
    except Exception as e:
        logger.warning("Could not connect to PostgreSQL: %s", e)
        paper_count = "N/A"

    try:
        async with VectorStore(DATABASE_URL) as vs:
            vector_count = await vs.count_vectors()
    except Exception as e:
        logger.warning("Could not connect to PostgreSQL (vector store): %s", e)
        vector_count = "N/A"

    click.echo(f"Papers in PostgreSQL: {paper_count}")
    click.echo(f"Papers with embeddings: {vector_count}")


# ─── Shared helpers ──────────────────────────────────────────────────────────


async def _store_papers(papers, vectors: list[list[float]]) -> None:
    """Store papers and their vectors in PostgreSQL (metadata + pgvector embeddings)."""
    from crawler.db import PaperStore
    from crawler.embedder import generate_embeddings_batch
    from crawler.vector_store import VectorStore

    # Store metadata in PostgreSQL
    paper_dicts = [p.to_dict() for p in papers]
    try:
        async with PaperStore(DATABASE_URL) as store:
            await store.upsert_papers_batch(paper_dicts)
    except Exception:
        logger.exception("Failed to store papers in PostgreSQL")
        # Continue to try vector store anyway

    # Store embeddings via pgvector
    if vectors:
        ids = [p.arxiv_id for p in papers]
        payloads = [
            {
                "title": p.title,
                "categories": p.categories,
                "published_at": p.published_at.isoformat() if p.published_at else "",
            }
            for p in papers
        ]
        try:
            async with VectorStore(DATABASE_URL) as vs:
                await vs.ensure_collection(vector_size=len(vectors[0]))
                await vs.upsert_papers(ids, vectors, payloads)
        except Exception:
            logger.exception("Failed to store vectors in pgvector")


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
