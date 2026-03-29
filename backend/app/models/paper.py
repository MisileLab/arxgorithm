from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class Category(str, Enum):
    cs_ai = "cs.AI"
    cs_cl = "cs.CL"
    cs_cv = "cs.CV"
    cs_lg = "cs.LG"
    cs_ne = "cs.NE"
    stat_ml = "stat.ML"


class Paper(BaseModel):
    arxiv_id: str = Field(..., description="arXiv paper ID (e.g. 2401.12345)")
    title: str
    abstract: str
    authors: list[str]
    categories: list[Category]
    published_at: datetime
    updated_at: datetime
    pdf_url: str
    embedding: list[float] | None = None


class PaperSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    categories: list[Category] | None = None


class PaperSearchResult(BaseModel):
    paper: Paper
    score: float = Field(..., description="Similarity score (0-1)")
