from fastapi import APIRouter, Depends
from app.models.paper import PaperSearchRequest, PaperSearchResult
from app.models.recommendation import RecommendationRequest, RecommendationResponse

router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/search", response_model=list[PaperSearchResult])
async def search_papers(request: PaperSearchRequest):
    """Search papers by semantic similarity."""
    # TODO: Implement vector search via HelixDB
    return []


@router.post("/recommend", response_model=RecommendationResponse)
async def recommend_papers(request: RecommendationRequest):
    """Get personalized paper recommendations."""
    # TODO: Implement collaborative filtering + agentic recommendation
    return RecommendationResponse(
        paper_ids=[],
        reasons=[],
        strategy="collaborative_filtering",
    )


@router.get("/{arxiv_id}")
async def get_paper(arxiv_id: str):
    """Get paper details by arXiv ID."""
    # TODO: Implement paper lookup
    return {"arxiv_id": arxiv_id}
