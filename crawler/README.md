# arxgorithm crawler

arXiv paper data pipeline — fetch, embed, store.

## Setup

```bash
pip install -r requirements.txt
python -m crawler.main
```

## What it does

1. Fetch paper metadata from arXiv API / bulk dump
2. Generate embeddings (title + abstract)
3. Store vectors in HelixDB
4. Store metadata in PostgreSQL
