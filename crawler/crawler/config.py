"""Shared configuration and constants."""

import os

# PostgreSQL
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://arxgorithm:***@localhost:5432/arxgorithm"
)

# DeepInfra Embedding API
DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY", "")
EMBEDDING_API_URL = os.environ.get(
    "EMBEDDING_API_URL", "https://api.deepinfra.com/v1/openai/embeddings"
)
DEFAULT_EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B"
)
EMBEDDING_BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", "64"))
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "1024"))

# ArXiv API
ARXIV_MAX_RESULTS_PER_PAGE = int(os.environ.get("ARXIV_MAX_RESULTS_PER_PAGE", "200"))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
