"""arxgorithm FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.papers import router as papers_router
from app.api.users import router as users_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise database tables."""
    # Import models so Base.metadata knows about them before create_all
    import app.models.db_models  # noqa: F401

    from app.core.database import init_db

    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Open-source personalized arXiv paper recommendation API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)
app.include_router(papers_router)
app.include_router(users_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
