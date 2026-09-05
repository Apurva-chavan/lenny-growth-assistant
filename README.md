# The Lenny Growth Assistant

A full-stack AI-powered conversational assistant that answers product and growth questions grounded in Lenny's Podcast transcripts, generates Ship 30 for 30–style essays, and renders Markdown/HTML artifacts in-app.

---

## Architecture Overview

```
frontend (React + Vite)  ──►  backend (FastAPI)  ──►  PostgreSQL
                                    │
                          ┌─────────┴──────────┐
                          │                    │
                     LLM Client           Knowledge Base
                  (Groq / Anthropic /     (FAISS + sentence-
                   OpenAI / Gemini)        transformers)
```

- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Backend**: FastAPI with async SQLAlchemy, structured logging via structlog
- **Agent layer**: Routes messages to RAG assistant, Ship30 skill, or Artifact skill
- **Knowledge base**: Transcript files chunked and indexed with sentence-transformers + FAISS (semantic search)
- **LLM**: Configurable via `LLM_PROVIDER` env var — `groq` (default/free), `anthropic`, `openai`, or `gemini`

---

## Live Demo

- Frontend: https://lenny-frontend-o809.onrender.com
- Backend API: https://lenny-growth-assistant-07l4.onrender.com/docs

---

## Deploy to Render (Free)

1. Fork or clone this repo to your GitHub
2. Go to https://render.com → New → Blueprint
3. Connect your GitHub repo — Render will detect `render.yaml` automatically
4. Set the `GROQ_API_KEY` environment variable in the Render dashboard for the `lenny-backend` service
5. Click Deploy

All three services (PostgreSQL, backend, frontend) deploy automatically.

Get a free Groq API key at: https://console.groq.com

---

## Run Locally

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2

### Steps

```bash
git clone https://github.com/Apurva-chavan/lenny-growth-assistant
cd lenny-growth-assistant

# Create .env
copy backend\.env.example backend\.env
# Edit backend/.env and set GROQ_API_KEY=your_key_here

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | Yes | `groq` | `groq` \| `anthropic` \| `openai` \| `gemini` |
| `DATABASE_URL` | Yes | see .env.example | PostgreSQL connection URL |
| `GROQ_API_KEY` | If provider=groq | — | Free at console.groq.com |
| `GROQ_MODEL` | No | `llama3-8b-8192` | Groq model name |
| `ANTHROPIC_API_KEY` | If provider=anthropic | — | Anthropic API key |
| `OPENAI_API_KEY` | If provider=openai | — | OpenAI API key |
| `GEMINI_API_KEY` | If provider=gemini | — | Google AI Studio key |
| `TRANSCRIPTS_DIR` | No | `/app/data/transcripts` | Path to transcript files |
| `TOP_K_RESULTS` | No | `5` | Number of chunks retrieved per query |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | CORS origins |

---

## Run Tests

```bash
docker compose exec backend pytest
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Backend fails to start | Check `DATABASE_URL` in `.env`; ensure postgres container is healthy |
| Empty answers | Transcript files are in `data/transcripts/` — index builds on startup |
| CORS errors | Add your frontend origin to `ALLOWED_ORIGINS` in `.env` |
| 429 from Groq | Free tier limit hit; wait a minute or switch model to `llama3-70b-8192` |

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agent/          # LLM client + routing agent
│   │   ├── api/            # FastAPI routers (sessions, messages, health)
│   │   ├── db/             # SQLAlchemy models, CRUD, database setup
│   │   ├── knowledge/      # Transcript ingestion + FAISS retriever
│   │   ├── skills/         # Ship30 essay skill, Artifact generation skill
│   │   ├── config.py
│   │   ├── logging_config.py
│   │   └── main.py
│   ├── tests/
│   ├── .env.example
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # API client
│   │   ├── components/     # Chat UI, ArtifactViewer, Sidebar
│   │   ├── hooks/          # useChat hook
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   └── nginx.conf
├── data/
│   └── transcripts/        # Lenny's Podcast transcript files
├── docs/
│   ├── PRD.md
│   ├── design.md
│   └── architecture.md
├── render.yaml             # One-click Render deployment
├── docker-compose.yml
└── README.md
```
