"""arXiv API client — async fetching with rate limiting, retry, and Atom XML parsing."""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator
from xml.etree import ElementTree

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
    "dc": "http://purl.org/dc/elements/1.1/",
}

# arXiv asks for 3-second spacing between requests; we use 5 to be safe.
MIN_REQUEST_INTERVAL = 5.0


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pdf_url: str = ""
    doi: str = ""
    journal_ref: str = ""
    comment: str = ""

    @property
    def embedding_text(self) -> str:
        """Combined text for embedding generation."""
        return f"{self.title.strip()}\n\n{self.abstract.strip()}"

    def to_dict(self) -> dict:
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "categories": self.categories,
            "published_at": self.published_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "pdf_url": self.pdf_url,
            "doi": self.doi,
            "journal_ref": self.journal_ref,
            "comment": self.comment,
        }


def _clean_whitespace(text: str) -> str:
    """Collapse whitespace in arXiv XML text fields."""
    return re.sub(r"\s+", " ", text).strip()


def _parse_entry(entry: ElementTree.Element) -> ArxivPaper | None:
    """Parse a single Atom <entry> element into an ArxivPaper."""
    try:
        ns = ARXIV_NS

        # ID — looks like "http://arxiv.org/abs/2401.12345v1"
        raw_id = entry.findtext("atom:id", namespaces=ns) or ""
        arxiv_id = raw_id.split("/abs/")[-1]
        # Strip version suffix for storage
        arxiv_id = re.sub(r"v\d+$", "", arxiv_id)

        title = _clean_whitespace(entry.findtext("atom:title", namespaces=ns) or "")
        abstract = _clean_whitespace(
            entry.findtext("atom:summary", namespaces=ns) or ""
        )

        authors = [
            _clean_whitespace(a.findtext("atom:name", namespaces=ns) or "")
            for a in entry.findall("atom:author", namespaces=ns)
        ]

        categories = [
            c.get("term", "")
            for c in entry.findall("atom:category", namespaces=ns)
            if c.get("term")
        ]

        published_raw = entry.findtext("atom:published", namespaces=ns) or ""
        updated_raw = entry.findtext("atom:updated", namespaces=ns) or ""
        published_at = datetime.fromisoformat(published_raw) if published_raw else datetime.now(timezone.utc)
        updated_at = datetime.fromisoformat(updated_raw) if updated_raw else datetime.now(timezone.utc)

        pdf_url = ""
        for link in entry.findall("atom:link", namespaces=ns):
            if link.get("title") == "pdf":
                pdf_url = link.get("href", "")
                break
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

        doi = entry.findtext("arxiv:doi", namespaces=ns) or ""
        journal_ref = entry.findtext("arxiv:journal_ref", namespaces=ns) or ""
        comment = entry.findtext("arxiv:comment", namespaces=ns) or ""

        return ArxivPaper(
            arxiv_id=arxiv_id,
            title=title,
            abstract=abstract,
            authors=authors,
            categories=categories,
            published_at=published_at,
            updated_at=updated_at,
            pdf_url=pdf_url,
            doi=doi,
            journal_ref=journal_ref,
            comment=comment,
        )
    except Exception:
        logger.exception("Failed to parse arXiv entry")
        return None


def parse_arxiv_response(xml_text: str) -> list[ArxivPaper]:
    """Parse full arXiv API Atom XML response into a list of papers."""
    root = ElementTree.fromstring(xml_text)
    entries = root.findall("atom:entry", namespaces=ARXIV_NS)
    papers: list[ArxivPaper] = []
    for entry in entries:
        paper = _parse_entry(entry)
        if paper is not None:
            papers.append(paper)
    return papers


class ArxivRateLimiter:
    """Simple rate limiter that enforces minimum interval between arXiv requests."""

    def __init__(self, min_interval: float = MIN_REQUEST_INTERVAL):
        self._min_interval = min_interval
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                logger.debug("Rate limiting: sleeping %.1fs", wait_time)
                await asyncio.sleep(wait_time)
            self._last_request_time = asyncio.get_event_loop().time()


class ArxivClient:
    """Async arXiv API client with rate limiting and retries."""

    def __init__(
        self,
        timeout: float = 60.0,
        max_results_per_page: int = 200,
        rate_limiter: ArxivRateLimiter | None = None,
    ):
        self._timeout = timeout
        self._max_results_per_page = max_results_per_page
        self._rate_limiter = rate_limiter or ArxivRateLimiter()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self._timeout, follow_redirects=True)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "ArxivClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    @retry(
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=3, min=5, max=120),
        before_sleep=lambda rs: logger.warning(
            "Retry %s after error: %s", rs.attempt_number, rs.outcome.exception()
        ),
    )
    async def _fetch_page(
        self,
        query: str,
        start: int,
        max_results: int,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> tuple[list[ArxivPaper], int]:
        """Fetch a single page of results. Returns (papers, total_results)."""
        await self._rate_limiter.acquire()

        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        client = await self._get_client()
        logger.info(
            "Fetching arXiv page: query=%r start=%d max=%d",
            query, start, max_results,
        )
        response = await client.get(ARXIV_API_URL, params=params)
        response.raise_for_status()

        # Parse total results from opensearch namespace
        total = 0
        try:
            root = ElementTree.fromstring(response.text)
            ns = {"opensearch": "http://a9.com/-/spec/opensearch/1.1/"}
            total_el = root.find("opensearch:totalResults", namespaces=ns)
            total = int(total_el.text) if total_el is not None else 0
        except Exception:
            pass

        papers = parse_arxiv_response(response.text)
        logger.info("Parsed %d papers (total reported: %d)", len(papers), total)
        return papers, total

    async def search(
        self,
        query: str,
        max_results: int = 100,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> AsyncIterator[list[ArxivPaper]]:
        """
        Search arXiv and yield batches of papers.

        Automatically paginates to collect up to max_results.
        Each yielded item is a list of papers (one page).
        """
        fetched = 0
        start = 0
        while fetched < max_results:
            batch_size = min(self._max_results_per_page, max_results - fetched)
            papers, total = await self._fetch_page(
                query, start, batch_size, sort_by, sort_order,
            )
            if not papers:
                break
            yield papers
            fetched += len(papers)
            start += len(papers)
            # If arXiv reports fewer total results than we need, stop
            if total > 0 and fetched >= total:
                break

    async def fetch_by_ids(self, arxiv_ids: list[str]) -> list[ArxivPaper]:
        """Fetch specific papers by their arXiv IDs."""
        id_list = ",".join(arxiv_ids)
        query = f"id_list={id_list}"

        await self._rate_limiter.acquire()

        client = await self._get_client()
        params = {
            "search_query": "",
            "id_list": id_list,
            "max_results": len(arxiv_ids),
        }
        response = await client.get(ARXIV_API_URL, params=params)
        response.raise_for_status()
        return parse_arxiv_response(response.text)


# Bulk dump support — parse arXiv bulk XML dumps

def parse_bulk_dump_file(path: str) -> list[ArxivPaper]:
    """
    Parse an arXiv bulk dump XML file.

    Bulk dumps are large XML files where each paper is wrapped in a
    standard structure. The format is similar to the API but the root
    element may vary.
    """
    papers: list[ArxivPaper] = []

    context = ElementTree.iterparse(path, events=("end",))
    for event, elem in context:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag == "entry" or tag == "record":
            paper = _parse_entry(elem) or _parse_bulk_record(elem)
            if paper is not None:
                papers.append(paper)
            elem.clear()
    return papers


def _parse_bulk_record(elem: ElementTree.Element) -> ArxivPaper | None:
    """Fallback parser for non-standard bulk dump record formats."""
    try:
        # Try direct field access without namespace
        def text(tag: str) -> str:
            # Try both namespaced and non-namespaced
            for ns_prefix in ["", "{http://www.w3.org/2005/Atom}"]:
                el = elem.find(f"{ns_prefix}{tag}")
                if el is not None and el.text:
                    return el.text
            return ""

        raw_id = text("id")
        arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id
        arxiv_id = re.sub(r"v\d+$", "", arxiv_id)

        title = _clean_whitespace(text("title"))
        abstract = _clean_whitespace(text("summary") or text("abstract"))

        authors = []
        for a in elem.findall(".//{http://www.w3.org/2005/Atom}author") or elem.findall(".//author"):
            name = a.findtext(
                "{http://www.w3.org/2005/Atom}name"
            ) or a.findtext("name") or ""
            if name:
                authors.append(_clean_whitespace(name))

        if not title:
            return None

        return ArxivPaper(
            arxiv_id=arxiv_id,
            title=title,
            abstract=abstract,
            authors=authors,
        )
    except Exception:
        logger.exception("Failed to parse bulk record")
        return None
