"""Paper routes: search, recommend, get by arxiv_id."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DbSession
from app.models.db_models import Paper
from app.models.paper import Paper as PaperSchema
from app.models.paper import PaperSearchRequest, PaperSearchResult
from app.models.recommendation import RecommendationResponse
from app.services.recommendation_service import get_recommendations
from app.services.search_service import embed_query, search_similar_with_db

router = APIRouter(prefix="/papers", tags=["papers"])


# ── Helper ─────────────────────────────────────────────────────────────


def _paper_to_schema(p: Paper) -> PaperSchema:
    """Convert an ORM Paper to a Pydantic Paper schema."""
    return PaperSchema(
        arxiv_id=p.arxiv_id,
        title=p.title,
        abstract=p.abstract,
        authors=p.authors or [],
        categories=p.categories or [],
        published_at=p.published_at,
        updated_at=p.updated_at,
        pdf_url=p.pdf_url or f"https://arxiv.org/pdf/{p.arxiv_id}",
    )


# ── Routes ─────────────────────────────────────────────────────────────


@router.post("/search", response_model=list[PaperSearchResult])
async def search_papers(
    request: PaperSearchRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Search papers by semantic similarity via pgvector."""
    embedding = embed_query(request.query)

    category_filter = None
    if request.categories:
        category_filter = [c.value for c in request.categories]

    results = await search_similar_with_db(
        embedding,
        db,
        limit=request.limit,
        category_filter=category_filter,
    )

    return [
        PaperSearchResult(
            paper=_paper_to_schema(paper),
            score=score,
        )
        for paper, score in results
    ]


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_papers(
    limit: int = 10,
    categories: list[str] | None = None,
    db: DbSession = None,
    current_user: CurrentUser = None,
):
    """Get personalized paper recommendations for the authenticated user."""
    return await get_recommendations(
        user_id=current_user.id,
        db=db,
        limit=min(limit, 100),
        categories=categories,
    )


@router.get("/{arxiv_id}", response_model=PaperSchema)
async def get_paper(arxiv_id: str, db: DbSession):
    """Get paper details by arXiv ID."""
    result = await db.execute(select(Paper).where(Paper.arxiv_id == arxiv_id))
    paper = result.scalar_one_or_none()

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper {arxiv_id!r} not found",
        )

    return _paper_to_schema(paper)
