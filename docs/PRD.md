# Product Requirements Document — The Lenny Growth Assistant

## Forward Deployment Brief

### User and Problem

**Primary user**: Product managers, growth leads, and startup founders who regularly consume Lenny's Podcast content and want to extract actionable insights without re-listening to hours of audio or manually searching transcripts.

**Job to be done**: "When I have a product or growth question, I want a grounded answer from Lenny's interviews in under 30 seconds, without needing to remember which episode covered it."

**Pain removed**: Manual transcript search, context-switching between podcast apps and work tools, inability to generate reusable written content from podcast insights.

### Success Metric

- **Primary**: ≥70% of answered questions receive a source citation traceable to a specific transcript (grounding rate), measured by evaluator spot-check of 20 queries.
- **Secondary**: End-to-end response latency ≤8 seconds on local Ollama (llama3.2) for a standard RAG query.

### Assumptions

1. Transcript files are available as plain text (`.txt` or `.md`) — the assignment references a public GitHub repo.
2. The evaluator runs Docker on a machine with ≥8 GB RAM for Ollama.
3. "Ship 30 for 30" principles are encoded from the public guide; no proprietary content is used.
4. PostgreSQL is the persistence layer; no external vector database is required for the demo (TF-IDF retrieval is sufficient for a corpus of ~200 transcripts).
5. A single-user demo is acceptable — no authentication or multi-tenancy is required.

### Scope Choices

**Included:**
- RAG conversational assistant with source citations
- Ship 30 for 30 essay skill (~1,250 words, structured output)
- Artifact generation (Markdown + HTML) with sandboxed in-app viewer
- Session persistence in PostgreSQL
- Configurable LLM provider (Ollama / Anthropic / OpenAI) via env var
- Docker Compose one-command startup
- Structured logging and health endpoints

**Excluded:**
- User authentication (out of scope for internal demo)
- Real-time streaming responses (adds complexity; polling is sufficient for demo)
- Semantic/vector embeddings (TF-IDF retrieval is simpler to run locally without GPU)
- Mobile-optimized layout (desktop-first for evaluator demo)
- Transcript auto-refresh/webhook (manual ingest script is sufficient)

### Risks and Trade-offs

| Risk | Likelihood | Mitigation |
|---|---|---|
| Hallucination | Medium | Strict system prompt: answer only from retrieved context; cite source |
| Local model quality (Ollama) | High | llama3.2 is capable but weaker than Claude; Ship30 essays may be lower quality |
| Latency on local model | Medium | TF-IDF retrieval is fast; Ollama latency depends on hardware |
| Unsafe artifact rendering | Medium | HTML rendered in sandboxed `<iframe sandbox>` with no scripts allowed |
| Empty retrieval | Low | Graceful fallback message when no relevant chunks found |
| Database connection failure | Low | Startup logs error and continues; health endpoint reports DB status |

---

## 1. Objective

Build "The Lenny Growth Assistant" — a full-stack AI web application that ingests Lenny's Podcast transcripts, answers product/growth questions with source grounding, generates Ship 30 for 30 essays, and renders Markdown/HTML artifacts in-app.

---

## 2. User Flows

### 2.1 Grounded Q&A
1. User opens app → new session created automatically
2. User types a product/growth question
3. Backend retrieves top-K relevant transcript chunks
4. LLM generates answer citing source(s)
5. Response displayed with source attribution

### 2.2 Ship 30 Essay
1. User asks: "Write a Ship 30 essay about [topic]"
2. Agent routes to Ship30 skill
3. Skill retrieves relevant transcript context
4. LLM generates ~1,250-word essay following Ship30 principles
5. Essay displayed; user can request artifact export

### 2.3 Artifact Generation
1. User requests: "Create a markdown summary" or "Generate an HTML report"
2. Agent routes to Artifact skill
3. Artifact rendered in side panel (ArtifactViewer)
4. HTML artifacts sandboxed; Markdown rendered via react-markdown

### 2.4 New Chat
1. User clicks "New Chat" in sidebar
2. New session ID created; context reset
3. Previous sessions visible in sidebar (future: session history)

---

## 3. Acceptance Criteria

| # | Criterion |
|---|---|
| AC-1 | Health endpoint `GET /health` returns 200 with DB and index status |
| AC-2 | `POST /api/v1/sessions` creates a session and returns session_id |
| AC-3 | `POST /api/v1/sessions/{id}/messages` returns a grounded answer with source field |
| AC-4 | Answers for out-of-scope questions include "I don't have information on that in the transcripts" |
| AC-5 | Ship30 essay is ~1,250 words with hook, headings, bullets, bold emphasis |
| AC-6 | HTML artifacts render in sandboxed iframe; `<script>` tags are stripped |
| AC-7 | Switching `LLM_PROVIDER` in `.env` changes the model without code changes |
| AC-8 | `docker compose up --build` starts all services within 3 minutes |
| AC-9 | All conversations and messages are persisted in PostgreSQL |
| AC-10 | Structured JSON logs emitted for every request, retrieval, and LLM call |

---

## 4. Implementation Plan

| Phase | Tasks | Status |
|---|---|---|
| 1. Scaffold | Directory structure, Docker Compose, env config | ✅ Done |
| 2. Backend core | FastAPI app, DB models, CRUD, health endpoint | ✅ Done |
| 3. Knowledge base | Transcript loader, chunker, TF-IDF retriever | ✅ Done |
| 4. Agent layer | LLM client abstraction, routing agent | ✅ Done |
| 5. Skills | Ship30 skill, Artifact skill | ✅ Done |
| 6. API routes | Sessions, messages endpoints | ✅ Done |
| 7. Frontend | React app, chat UI, ArtifactViewer | ✅ Done |
| 8. Docs | README, PRD, design.md, architecture.md | ✅ Done |
| 9. Tests | API tests, retrieval tests | ✅ Done |
