"""arXiv API client for fetching paper metadata."""

import logging
from dataclasses import dataclass
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

ARXIV_API_URL = "http://export.arxiv.org/api/query"


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    published_at: datetime
    updated_at: datetime
    pdf_url: str


async def fetch_papers(
    query: str,
    max_results: int = 100,
    start: int = 0,
) -> list[ArxivPaper]:
    """Fetch papers from arXiv API."""
    # TODO: Implement actual API parsing
    logger.info(f"Fetching papers: query={query}, max={max_results}")
    return []
