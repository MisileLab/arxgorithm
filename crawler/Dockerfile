# ── Stage 1: Install dependencies ───────────────────────────────
FROM python:3.14-slim AS deps

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# ── Stage 2: Production image ──────────────────────────────────
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --shell /bin/bash app

WORKDIR /app

COPY --from=deps /app/.venv /app/.venv
COPY pyproject.toml ./
COPY crawler/ crawler/

ENV PATH="/app/.venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

USER app

ENTRYPOINT ["uv", "run", "crawl"]
CMD ["schedule"]
