"""Recommendation service: collaborative filtering + content-based + agentic reasoning."""

from __future__ import annotations

import json
import logging
import uuid
from collections import Counter
from datetime import datetime, timezone

from openai import OpenAI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embedding import embed_text
from app.models.db_models import Interaction, InteractionType, Paper, ReadingHistory, User
from app.models.recommendation import RecommendationReason, RecommendationResponse

logger = logging.getLogger(__name__)

# Module-level OpenAI client for LLM calls
_llm_client = OpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
)


# ── Collaborative Filtering ────────────────────────────────────────────


async def collaborative_filter(
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 20,
) -> list[str]:
    """
    Find users with overlapping reading history and recommend papers they
    have read that the target user has not.

    Returns a list of arxiv_id strings, most commonly co-read first.
    """
    # Papers the user has already read
    user_papers_stmt = select(ReadingHistory.paper_id).where(
        ReadingHistory.user_id == user_id
    )
    result = await db.execute(user_papers_stmt)
    user_paper_ids = set(result.scalars().all())

    if not user_paper_ids:
        return []

    # Find other users who read the same papers
    similar_users_stmt = (
        select(ReadingHistory.user_id)
        .where(
            ReadingHistory.paper_id.in_(user_paper_ids),
            ReadingHistory.user_id != user_id,
        )
        .group_by(ReadingHistory.user_id)
        .order_by(func.count(ReadingHistory.paper_id).desc())
        .limit(50)
    )
    result = await db.execute(similar_users_stmt)
    similar_user_ids = result.scalars().all()

    if not similar_user_ids:
        return []

    # Papers read by similar users that the target user hasn't read
    candidate_stmt = (
        select(ReadingHistory.paper_id)
        .where(
            ReadingHistory.user_id.in_(similar_user_ids),
            ~ReadingHistory.paper_id.in_(user_paper_ids),
        )
    )
    result = await db.execute(candidate_stmt)
    candidate_paper_ids = [row for row in result.scalars().all()]

    # Rank by frequency
    counts = Counter(candidate_paper_ids)
    top_ids = [pid for pid, _ in counts.most_common(limit)]

    if not top_ids:
        return []

    # Resolve to arxiv_ids
    paper_stmt = select(Paper.arxiv_id).where(Paper.id.in_(top_ids))
    result = await db.execute(paper_stmt)
    return list(result.scalars().all())[:limit]


# ── Content-Based Filtering ────────────────────────────────────────────


async def content_based_filter(
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 20,
) -> list[str]:
    """
    Build a profile embedding from the user's reading history and find
    similar papers via pgvector.
    """
    # Fetch papers the user has read
    stmt = (
        select(Paper)
        .join(ReadingHistory, ReadingHistory.paper_id == Paper.id)
        .where(ReadingHistory.user_id == user_id)
        .order_by(ReadingHistory.read_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    papers = result.scalars().all()

    if not papers:
        return []

    # Build a combined text from recent reads and embed it
    combined_text = " ".join(f"{p.title} {p.abstract}" for p in papers[:20])
    embedding = embed_text(combined_text)

    # Search for similar papers via pgvector
    from app.services.search_service import search_similar_with_db

    similar = await search_similar_with_db(
        embedding,
        db,
        limit=limit,
    )

    # Filter out papers the user already read
    read_ids = {p.arxiv_id for p in papers}
    return [p.arxiv_id for p, _score in similar if p.arxiv_id not in read_ids][:limit]


# ── Agentic Reasoning ──────────────────────────────────────────────────


async def agentic_reason(
    paper_ids: list[str],
    user_context: str,
    db: AsyncSession,
) -> list[RecommendationReason]:
    """
    Call an OpenAI-compatible LLM to generate human-readable explanations
    for why each paper is recommended.
    """
    if not paper_ids:
        return []

    # Fetch paper metadata for context
    stmt = select(Paper).where(Paper.arxiv_id.in_(paper_ids))
    result = await db.execute(stmt)
    papers = result.scalars().all()
    paper_map = {p.arxiv_id: p for p in papers}

    # Build prompt
    paper_summaries = []
    for pid in paper_ids:
        p = paper_map.get(pid)
        if p:
            paper_summaries.append(
                f"- {p.arxiv_id}: \"{p.title}\" | {p.abstract[:300]}"
            )
        else:
            paper_summaries.append(f"- {pid}: (metadata not found)")

    prompt = (
        "You are a helpful research assistant. Given a user's research context "
        "and a list of recommended papers, provide a brief (1-2 sentence) reason "
        "for why each paper is relevant to the user.\n\n"
        f"User context: {user_context}\n\n"
        "Papers:\n" + "\n".join(paper_summaries) + "\n\n"
        "Respond with a JSON array of objects, each with 'paper_id' and 'reason' keys. "
        "Example: [{\"paper_id\": \"2401.12345\", \"reason\": \"...\"}]"
    )

    reasons: list[RecommendationReason] = []

    try:
        completion = _llm_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": "You are a JSON-only response engine."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        content = completion.choices[0].message.content

        # Try to parse JSON from the response
        parsed = json.loads(content)
        if isinstance(parsed, list):
            for item in parsed:
                reasons.append(
                    RecommendationReason(
                        paper_id=item.get("paper_id", ""),
                        reason=item.get("reason", ""),
                    )
                )
    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        logger.warning("Agentic reasoning failed: %s – using fallback reasons", exc)
        # Fallback: generate simple reasons
        for pid in paper_ids:
            p = paper_map.get(pid)
            title = p.title if p else pid
            reasons.append(
                RecommendationReason(
                    paper_id=pid,
                    reason=f"Recommended based on similarity to your reading history: \"{title}\"",
                )
            )
    except Exception as exc:
        logger.warning("Agentic reasoning LLM call failed: %s – using fallback reasons", exc)
        # Fallback: generate simple reasons
        for pid in paper_ids:
            p = paper_map.get(pid)
            title = p.title if p else pid
            reasons.append(
                RecommendationReason(
                    paper_id=pid,
                    reason=f"Recommended based on similarity to your reading history: \"{title}\"",
                )
            )

    return reasons


# ── Top-level orchestration ────────────────────────────────────────────


async def get_recommendations(
    user_id: uuid.UUID,
    db: AsyncSession,
    *,
    limit: int = 10,
    categories: list[str] | None = None,
) -> RecommendationResponse:
    """
    Combine collaborative filtering, content-based filtering, and agentic
    reasoning into a single recommendation response.
    """
    # Gather candidates from both strategies
    cf_ids = await collaborative_filter(user_id, db, limit=limit)
    cb_ids = await content_based_filter(user_id, db, limit=limit)

    # Merge with CF given priority, deduplicate while preserving order
    seen: set[str] = set()
    merged: list[str] = []
    for pid in cf_ids + cb_ids:
        if pid not in seen:
            seen.add(pid)
            merged.append(pid)
        if len(merged) >= limit:
            break

    # Apply category filter if provided
    if categories:
        cat_set = set(categories)
        stmt = select(Paper.arxiv_id).where(Paper.arxiv_id.in_(merged))
        result = await db.execute(stmt)
        papers = result.scalars().all()
        # Filter on categories stored in DB
        filtered = []
        for p_obj in papers:
            cats = set(p_obj.categories or [])
            if cats & cat_set:
                filtered.append(p_obj.arxiv_id)
        merged = [pid for pid in merged if pid in set(filtered)][:limit]

    # Build user context for agentic reasoning
    history_stmt = (
        select(Paper)
        .join(ReadingHistory, ReadingHistory.paper_id == Paper.id)
        .where(ReadingHistory.user_id == user_id)
        .order_by(ReadingHistory.read_at.desc())
        .limit(10)
    )
    result = await db.execute(history_stmt)
    recent_papers = result.scalars().all()
    user_context = "Recent readings: " + "; ".join(
        p.title for p in recent_papers
    ) if recent_papers else "New user with no reading history."

    # Generate agentic explanations
    reasons = await agentic_reason(merged, user_context, db)

    strategy = "hybrid" if cf_ids and cb_ids else (
        "collaborative_filtering" if cf_ids else
        "content_based" if cb_ids else "none"
    )

    return RecommendationResponse(
        paper_ids=merged,
        reasons=reasons,
        strategy=strategy,
    )
