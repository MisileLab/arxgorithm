"""SQLAlchemy ORM models for arxgorithm."""

import enum
import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base


# ── Enums ──────────────────────────────────────────────────────────────

class InteractionType(str, enum.Enum):
    view = "view"
    bookmark = "bookmark"
    like = "like"
    share = "share"


# ── Mixin for timestamps ───────────────────────────────────────────────

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


# ── User ───────────────────────────────────────────────────────────────

class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)

    # relationships
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark", back_populates="user", cascade="all, delete-orphan"
    )
    reading_history: Mapped[list["ReadingHistory"]] = relationship(
        "ReadingHistory", back_populates="user", cascade="all, delete-orphan"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"


# ── Paper ──────────────────────────────────────────────────────────────

class Paper(TimestampMixin, Base):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    arxiv_id: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False, default="")
    authors: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    categories: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # pgvector embedding column
    embedding = mapped_column(Vector(settings.embedding_dimension), nullable=True)

    # relationships
    bookmarks: Mapped[list["Bookmark"]] = relationship(
        "Bookmark", back_populates="paper", cascade="all, delete-orphan"
    )
    reading_history: Mapped[list["ReadingHistory"]] = relationship(
        "ReadingHistory", back_populates="paper", cascade="all, delete-orphan"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="paper", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Paper {self.arxiv_id!r}>"


# ── Bookmark ───────────────────────────────────────────────────────────

class Bookmark(TimestampMixin, Base):
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_bookmark_user_paper"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="bookmarks")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="bookmarks")

    def __repr__(self) -> str:
        return f"<Bookmark user={self.user_id} paper={self.paper_id}>"


# ── ReadingHistory ─────────────────────────────────────────────────────

class ReadingHistory(TimestampMixin, Base):
    __tablename__ = "reading_history"
    __table_args__ = (
        UniqueConstraint("user_id", "paper_id", name="uq_reading_history_user_paper"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="reading_history")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="reading_history")

    def __repr__(self) -> str:
        return f"<ReadingHistory user={self.user_id} paper={self.paper_id}>"


# ── Interaction ────────────────────────────────────────────────────────

class Interaction(TimestampMixin, Base):
    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("papers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[InteractionType] = mapped_column(
        Enum(InteractionType, name="interaction_type"),
        nullable=False,
        index=True,
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="interactions")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="interactions")

    def __repr__(self) -> str:
        return f"<Interaction user={self.user_id} paper={self.paper_id} type={self.type.value}>"
