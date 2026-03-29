# arxgorithm 📚

> Open-source personalized arXiv paper recommendation platform

arxgorithm은 arXiv 논문을 개인화하여 추천하는 오픈소스 웹 플랫폼입니다. 협업 필터링 임베딩과 에이전틱 추천을 결합하여 연구자에게 맞춤형 논문을 제안합니다.

## ✨ Features

- **개인화 피드** — 관심 주제/키워드 기반 맞춤 추천
- **협업 필터링** — "이 논문을 읽은 사람들이 같이 읽은 논문" 추천
- **임베딩 검색** — 논문 title + abstract 기반 벡터 유사도 검색
- **에이전틱 추천** — LLM 에이전트가 추천 이유를 설명
- **논문 관리** — 북마크, 메모, 인용 그래프 시각화
- **커뮤니티** — 리뷰, 토론, 추천 리스트 공유

## 🛠 Tech Stack

| Area | Technology |
|------|-----------|
| Frontend | React Router v7 |
| Backend | FastAPI (Python) |
| Vector DB | HelixDB |
| Embedding | Sentence Transformers / OpenAI |
| LLM Agent | OpenAI / Anthropic API |
| Crawling | arXiv API + bulk dump |
| Auth | OAuth (Google, GitHub, ORCID) |
| Deploy | Docker + docker-compose |

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/MisileLab/arxgorithm.git
cd arxgorithm

# Docker Compose (one-click)
docker-compose up -d
```

## 📁 Project Structure

```
arxgorithm/
├── frontend/          # React Router v7 app
├── backend/           # FastAPI server
├── crawler/           # arXiv data pipeline
├── docs/              # PDD, architecture docs
├── docker-compose.yml
└── LICENSE            # AGPL-3.0
```

## 📜 License

AGPL-3.0 — 셀프호스팅 가능, 수정사항 공유 의무.

## 🤝 Contributing

PRs welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.
