# Contributing to arxgorithm

Thank you for your interest! Here's how to get started.

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Crawler

```bash
cd crawler
pip install -r requirements.txt
python -m crawler.main
```

## Code Style

- **Python**: Ruff (lint + format), type hints required
- **TypeScript**: ESLint + Prettier
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)

## Pull Request Process

1. Fork the repo
2. Create a feature branch (`feat/your-feature`)
3. Write tests for new functionality
4. Ensure all tests pass: `pytest` (backend), `npm test` (frontend)
5. Submit PR with a clear description

## Reporting Issues

Use GitHub Issues with appropriate labels:
- `bug` — Something broken
- `feature` — New feature request
- `question` — General questions

## License

By contributing, you agree your code will be licensed under AGPL-3.0.
