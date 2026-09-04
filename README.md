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
                  (Anthropic/OpenAI/      (TF-IDF retriever
                     Ollama)               over transcripts)
```

- **Frontend**: React 18 + TypeScript + Tailwind CSS, served via Nginx
- **Backend**: FastAPI with async SQLAlchemy, structured logging via structlog
- **Agent layer**: Routes messages to RAG assistant, Ship30 skill, or Artifact skill
- **Knowledge base**: Transcript files chunked and indexed with sentence-transformers + FAISS (semantic search, runs locally, no GPU needed)
- **LLM**: Configurable via `LLM_PROVIDER` env var — `ollama` (default/demo), `anthropic`, or `openai`

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- [Ollama](https://ollama.com) installed locally (for local demo)
- Git

---

## Installation

```bash
git clone <your-repo-url>
cd "assignmnet 1"
```

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env — set LLM_PROVIDER and any API keys
```

### 2. Add transcripts

Place Lenny's Podcast transcript `.txt` or `.md` files in:

```
data/transcripts/
```

Download from: https://github.com/lennyspodcast/transcripts (or any public source)

### 3. One-command startup

```bash
docker compose up --build
```

The app will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | Yes | `ollama` | `ollama` \| `anthropic` \| `openai` |
| `DATABASE_URL` | Yes | see .env.example | PostgreSQL async URL |
| `ANTHROPIC_API_KEY` | If provider=anthropic | — | Anthropic API key |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-20241022` | Model name |
| `OPENAI_API_KEY` | If provider=openai | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o` | Model name |
| `OLLAMA_BASE_URL` | If provider=ollama | `http://ollama:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | No | `llama3.2` | Ollama model name |
| `TRANSCRIPTS_DIR` | No | `/app/data/transcripts` | Path to transcript files |
| `TOP_K_RESULTS` | No | `5` | Number of chunks retrieved per query |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000,...` | CORS origins |

---

## Local Ollama Setup (Demo)

```bash
# Pull a model (llama3.2 works well on most machines)
ollama pull llama3.2

# Verify it runs
ollama run llama3.2 "Hello"
```

When running via Docker Compose, Ollama runs as a container. The backend connects to it at `http://ollama:11434`.

To switch to Anthropic Claude:
```bash
# In backend/.env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

No code changes required — the provider is read at startup.

---

## Ingest Transcripts

After adding transcript files to `data/transcripts/`:

```bash
# Rebuild the knowledge index inside the running backend container
docker compose exec backend python -c "from app.knowledge.retriever import build_index; build_index(force=True)"

# Or use the helper script (Linux/Mac/WSL)
bash scripts/ingest.sh
```

---

## Run Tests

```bash
docker compose exec backend pytest
```

Or locally:
```bash
cd backend
pip install -r requirements.txt
pytest
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Backend fails to start | Check `DATABASE_URL` in `.env`; ensure postgres container is healthy |
| Ollama timeout | Run `ollama pull llama3.2` first; increase `OLLAMA_TIMEOUT` if needed |
| Empty answers | Ensure transcript files exist in `data/transcripts/` and index was built |
| CORS errors | Add your frontend origin to `ALLOWED_ORIGINS` in `.env` |
| 429 from cloud LLM | Check API key quota; switch to `LLM_PROVIDER=ollama` for local demo |

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── agent/          # LLM client + routing agent
│   │   ├── api/            # FastAPI routers (sessions, messages, health)
│   │   ├── db/             # SQLAlchemy models, CRUD, database setup
│   │   ├── knowledge/      # Transcript ingestion + TF-IDF retriever
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
│   └── transcripts/        # Place .txt/.md transcript files here
├── docs/
│   ├── PRD.md
│   ├── design.md
│   └── architecture.md
├── scripts/
│   ├── setup.sh
│   └── ingest.sh
├── agent_transcripts/      # Coding agent session logs
├── docker-compose.yml
└── README.md
```
