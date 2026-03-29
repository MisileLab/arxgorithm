# arxgorithm crawler

arXiv paper data pipeline — fetch, embed, store.

## Setup (with uv)

```bash
# Install dependencies
uv sync

# Or just run directly
uv run crawl --help
```

## Commands

```bash
# Search arXiv and store results
uv run crawl search --query "cat:cs.AI" --max 100

# Search with custom sort
uv run crawl search --query "ti:transformer" --sort-by relevance --max 50

# Process a bulk arXiv dump
uv run crawl bulk --path /data/arxiv-dump.xml

# Generate embeddings for stored papers
uv run crawl embed --model all-MiniLM-L6-v2

# Show statistics
uv run crawl stats
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://arxgorithm:arxgorithm@localhost:5432/arxgorithm` | PostgreSQL connection string |
| `HELIXDB_URL` | `http://localhost:6334` | HelixDB REST API URL |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `EMBEDDING_BATCH_SIZE` | `64` | Batch size for embedding generation |
| `EMBEDDING_DIMENSION` | `384` | Embedding vector dimension |
| `LOG_LEVEL` | `INFO` | Logging level |

## What it does

1. Fetch paper metadata from arXiv API (Atom XML) or bulk dumps
2. Generate embeddings (title + abstract) using sentence-transformers
3. Store vectors in HelixDB (vector database, REST API on port 6334)
4. Store metadata in PostgreSQL (asyncpg)
5. Full CLI with search, bulk processing, and embedding commands

## Architecture

```
crawler/
  __init__.py        # Package init
  main.py            # CLI entry point (click)
  arxiv_client.py    # Async arXiv API client with rate limiting
  embedder.py        # Sentence-transformers embedding pipeline
  db.py              # PostgreSQL storage via asyncpg
  vector_store.py    # HelixDB vector storage via httpx
  config.py          # Configuration from environment
```
