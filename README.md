# arxgorithm 📚

> Open-source personalized arXiv paper recommendation platform

arxgorithm은 arXiv 논문을 개인화하여 추천하는 오픈소스 웹 플랫폼입니다. 협업 필터링, 임베딩 검색, 에이전틱 추천을 결합하여 연구자에게 맞춤형 논문을 제안합니다.

## ✨ Features

- **시맨틱 검색** — 논문 title + abstract 기반 벡터 유사도 검색
- **협업 필터링** — "이 논문을 읽은 사람들이 같이 읽은 논문" 추천
- **콘텐츠 기반 필터링** — 읽은 논문의 임베딩으로 관련 논문 발견
- **에이전틱 추천** — LLM이 추천 이유를 자연어로 설명
- **논문 관리** — 북마크, 읽은 기록, 카테고리 필터
- **arXiv 크롤러** — API 검색 + bulk dump 처리

## 🛠 Tech Stack

| Area | Technology |
|------|-----------|
| Frontend | React Router v7, Tailwind CSS |
| Backend | FastAPI (Python), SQLAlchemy async |
| Vector DB | HelixDB |
| Embedding | Sentence Transformers (all-MiniLM-L6-v2) |
| LLM Agent | OpenAI-compatible API |
| Crawling | arXiv API + bulk XML dump |
| Database | PostgreSQL 16 |
| Package Manager | uv (Python), npm (JS) |
| Deploy | Docker Compose |

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/MisileLab/arxgorithm.git
cd arxgorithm

# Start all services
docker compose up -d

# Run crawler to fetch papers
docker compose --profile crawler run crawler search "attention transformer" --max-results 50
```

### Local Development

```bash
# Backend
cd backend
uv sync
uvicorn app.main:app --reload

# Crawler
cd crawler
uv sync
python -m crawler.main search "machine learning" --max-results 20

# Frontend
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
arxgorithm/
├── frontend/              # React Router v7 app
│   └── app/
│       ├── components/    # PaperCard, SearchBar
│       ├── routes/        # home, search, feed, paper detail, bookmarks, auth
│       └── lib/           # API client, auth context
├── backend/               # FastAPI server
│   └── app/
│       ├── api/           # Routes: auth, papers, users
│       ├── core/          # Config, database, security, embedding
│       ├── models/        # Pydantic schemas + SQLAlchemy ORM models
│       └── services/      # Search, recommendation engine
├── crawler/               # arXiv data pipeline
│   └── crawler/
│       ├── arxiv_client.py  # arXiv API client
│       ├── embedder.py      # Sentence-transformers pipeline
│       ├── db.py            # PostgreSQL storage
│       └── vector_store.py  # HelixDB client
├── docs/                  # PDD, architecture docs
├── docker-compose.yml
└── LICENSE                # AGPL-3.0
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /papers/search | Semantic paper search |
| POST | /papers/recommend | Personalized recommendations |
| GET | /papers/{arxiv_id} | Paper details |
| POST | /auth/register | User registration |
| POST | /auth/login | Login (returns JWT) |
| GET | /auth/me | Current user profile |
| GET | /users/me/bookmarks | List bookmarks |
| POST | /users/me/bookmarks/{arxiv_id} | Add bookmark |
| GET | /users/me/history | Reading history |

## 📜 License

AGPL-3.0 — 셀프호스팅 가능, 수정사항 공유 의무.

## 🤝 Contributing

PRs welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.
