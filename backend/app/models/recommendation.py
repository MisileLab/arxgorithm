from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    user_id: str
    limit: int = Field(default=10, ge=1, le=100)
    categories: list[str] | None = None


class RecommendationReason(BaseModel):
    paper_id: str
    reason: str = Field(..., description="Why this paper is recommended")


class RecommendationResponse(BaseModel):
    paper_ids: list[str]
    reasons: list[RecommendationReason]
    strategy: str = Field(..., description="Recommendation strategy used")
