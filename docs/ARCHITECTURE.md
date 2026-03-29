# Architecture

```
┌──────────────────────────────────┐
│     React Router Frontend        │
│     (port 3000)                  │
└────────────┬─────────────────────┘
             ↕ REST API
┌──────────────────────────────────┐
│     FastAPI Backend              │
│     (port 8000)                  │
│  ┌─────────┐ ┌────────────────┐ │
│  │ Papers  │ │ Recommendations│ │
│  │ API     │ │ API            │ │
│  └────┬────┘ └───────┬────────┘ │
└───────┼──────────────┼──────────┘
        ↕              ↕
┌──────────────┐ ┌──────────────┐
│   HelixDB    │ │  LLM Agent   │
│  (vectors)   │ │ (reasoning)  │
└──────────────┘ └──────────────┘
        ↕
┌──────────────────────────────────┐
│   PostgreSQL                     │
│   (users, bookmarks, history)   │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│   Crawler (background)           │
│   arXiv API → Embed → Store     │
└──────────────────────────────────┘
```

## Data Pipeline

1. Crawler fetches papers from arXiv API / bulk dump
2. Embedding generated from title + abstract
3. Vectors stored in HelixDB
4. Metadata stored in PostgreSQL
5. User interactions update collaborative filtering matrix
6. LLM agent generates recommendation reasoning
