"""Shared configuration and constants."""

import os

# HelixDB
HELIXDB_URL = os.environ.get("HELIXDB_URL", "http://localhost:6334")

# PostgreSQL
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://arxgorithm:arxgorithm@localhost:5432/arxgorithm"
)

# Embedding
DEFAULT_EMBEDDING_MODEL = os.environ.get(
    "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
)
EMBEDDING_BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE", "64"))
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "384"))

# ArXiv API
ARXIV_MAX_RESULTS_PER_PAGE = int(os.environ.get("ARXIV_MAX_RESULTS_PER_PAGE", "200"))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
