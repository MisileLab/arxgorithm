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
uv run crawl embed --model Qwen/Qwen3-Embedding-0.6B

# Show statistics
uv run crawl stats
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://arxgorithm:***@localhost:5432/arxgorithm` | PostgreSQL connection string |
| `EMBEDDING_MODEL` | `Qwen/Qwen3-Embedding-0.6B` | Embedding model name |
| `EMBEDDING_BATCH_SIZE` | `64` | Batch size for embedding generation |
| `EMBEDDING_DIMENSION` | `1024` | Embedding vector dimension |
| `LOG_LEVEL` | `INFO` | Logging level |

## What it does

1. Fetch paper metadata from arXiv API (Atom XML) or bulk dumps
2. Generate embeddings (title + abstract) using DeepInfra API (Qwen3-Embedding-0.6B)
3. Store embeddings in PostgreSQL via pgvector
4. Store metadata in PostgreSQL (asyncpg)
5. Full CLI with search, bulk processing, and embedding commands

## Architecture

```
crawler/
  __init__.py        # Package init
  main.py            # CLI entry point (click)
  arxiv_client.py    # Async arXiv API client with rate limiting
  embedder.py        # DeepInfra embedding pipeline
  db.py              # PostgreSQL storage via asyncpg
  vector_store.py    # pgvector embedding storage via asyncpg
  config.py          # Configuration from environment
```
