"""User routes: bookmarks and reading history."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DbSession
from app.models.db_models import Bookmark, Paper, ReadingHistory

router = APIRouter(prefix="/users", tags=["users"])


# ── Response schemas ───────────────────────────────────────────────────


class BookmarkResponse(BaseModel):
    arxiv_id: str
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    arxiv_id: str
    title: str
    read_at: datetime

    model_config = {"from_attributes": True}


# ── Helpers ────────────────────────────────────────────────────────────


def _make_bookmark_resp(b: Bookmark) -> BookmarkResponse:
    return BookmarkResponse(
        arxiv_id=b.paper.arxiv_id,
        title=b.paper.title,
        created_at=b.created_at,
    )


def _make_history_resp(h: ReadingHistory) -> HistoryResponse:
    return HistoryResponse(
        arxiv_id=h.paper.arxiv_id,
        title=h.paper.title,
        read_at=h.read_at,
    )


# ── Bookmarks ──────────────────────────────────────────────────────────


@router.get("/me/bookmarks", response_model=list[BookmarkResponse])
async def list_bookmarks(current_user: CurrentUser, db: DbSession):
    """List the current user's bookmarked papers."""
    stmt = (
        select(Bookmark)
        .where(Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
    )
    result = await db.execute(stmt)
    bookmarks = result.scalars().all()

    # Eager-load related papers
    resp: list[BookmarkResponse] = []
    for b in bookmarks:
        paper_result = await db.execute(select(Paper).where(Paper.id == b.paper_id))
        paper = paper_result.scalar_one_or_none()
        if paper:
            resp.append(
                BookmarkResponse(
                    arxiv_id=paper.arxiv_id,
                    title=paper.title,
                    created_at=b.created_at,
                )
            )
    return resp


@router.post("/me/bookmarks/{arxiv_id}", status_code=status.HTTP_201_CREATED)
async def add_bookmark(arxiv_id: str, current_user: CurrentUser, db: DbSession):
    """Bookmark a paper by arXiv ID."""
    # Find the paper
    result = await db.execute(select(Paper).where(Paper.arxiv_id == arxiv_id))
    paper = result.scalar_one_or_none()
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper {arxiv_id!r} not found",
        )

    # Check for existing bookmark
    existing = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.paper_id == paper.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Paper already bookmarked",
        )

    bookmark = Bookmark(user_id=current_user.id, paper_id=paper.id)
    db.add(bookmark)
    await db.flush()

    return {"detail": "Bookmarked", "arxiv_id": arxiv_id}


@router.delete("/me/bookmarks/{arxiv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(arxiv_id: str, current_user: CurrentUser, db: DbSession):
    """Remove a bookmark by arXiv ID."""
    # Find the paper
    result = await db.execute(select(Paper).where(Paper.arxiv_id == arxiv_id))
    paper = result.scalar_one_or_none()
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper {arxiv_id!r} not found",
        )

    result = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.paper_id == paper.id,
        )
    )
    bookmark = result.scalar_one_or_none()
    if bookmark is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found",
        )

    await db.delete(bookmark)
    await db.flush()


# ── Reading History ────────────────────────────────────────────────────


@router.get("/me/history", response_model=list[HistoryResponse])
async def list_history(current_user: CurrentUser, db: DbSession):
    """List the current user's reading history."""
    stmt = (
        select(ReadingHistory)
        .where(ReadingHistory.user_id == current_user.id)
        .order_by(ReadingHistory.read_at.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    history = result.scalars().all()

    resp: list[HistoryResponse] = []
    for h in history:
        paper_result = await db.execute(select(Paper).where(Paper.id == h.paper_id))
        paper = paper_result.scalar_one_or_none()
        if paper:
            resp.append(
                HistoryResponse(
                    arxiv_id=paper.arxiv_id,
                    title=paper.title,
                    read_at=h.read_at,
                )
            )
    return resp


@router.post("/me/history/{arxiv_id}", status_code=status.HTTP_201_CREATED)
async def add_history(arxiv_id: str, current_user: CurrentUser, db: DbSession):
    """Record that the user has read a paper (upsert by unique constraint)."""
    result = await db.execute(select(Paper).where(Paper.arxiv_id == arxiv_id))
    paper = result.scalar_one_or_none()
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper {arxiv_id!r} not found",
        )

    # Upsert: if already exists, update read_at timestamp
    existing = await db.execute(
        select(ReadingHistory).where(
            ReadingHistory.user_id == current_user.id,
            ReadingHistory.paper_id == paper.id,
        )
    )
    entry = existing.scalar_one_or_none()
    if entry is not None:
        entry.read_at = datetime.now(timezone.utc)
        await db.flush()
        return {"detail": "History updated", "arxiv_id": arxiv_id}

    entry = ReadingHistory(
        user_id=current_user.id,
        paper_id=paper.id,
    )
    db.add(entry)
    await db.flush()

    return {"detail": "History recorded", "arxiv_id": arxiv_id}
