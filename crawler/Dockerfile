FROM python:3.14-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project definition first for layer caching
COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project

# Copy source code
COPY crawler/ crawler/
RUN uv sync --no-dev

ENTRYPOINT ["uv", "run", "crawl"]
