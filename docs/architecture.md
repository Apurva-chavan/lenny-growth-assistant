# Architecture Document — The Lenny Growth Assistant

## Database Schema

### `sessions` table
| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR(36) PK | UUID v4 |
| `title` | VARCHAR(255) | Default "New Chat" |
| `user_metadata` | JSON | Extensible user context |
| `llm_provider` | VARCHAR(50) | Provider used for this session |
| `created_at` | DATETIME | |
| `updated_at` | DATETIME | Auto-updated on change |

### `messages` table
| Column | Type | Notes |
|---|---|---|
| `id` | VARCHAR(36) PK | UUID v4 |
| `session_id` | VARCHAR(36) FK → sessions.id | CASCADE delete |
| `role` | VARCHAR(20) | `user` or `assistant` |
| `content` | TEXT | Message body |
| `sources` | JSON | Array of `{source, url, excerpt}` |
| `artifact` | JSON (nullable) | `{type: "html"|"markdown", content: "..."}` |
| `created_at` | DATETIME | |

---

## API Endpoints

### Health
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Returns DB status, index status, LLM provider, Ollama availability |

### Sessions
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/sessions` | Create a new chat session |
| GET | `/api/v1/sessions` | List all sessions |
| GET | `/api/v1/sessions/{id}` | Get session with messages |
| DELETE | `/api/v1/sessions/{id}` | Delete session and messages |

### Messages
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/sessions/{id}/messages` | Send a message; returns assistant reply |
| GET | `/api/v1/sessions/{id}/messages` | List messages in session |

### Request/Response Contracts

**POST /api/v1/sessions/{id}/messages**

Request:
```json
{ "content": "What does Lenny say about retention?" }
```

Response:
```json
{
  "message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "According to the transcript with Brian Balfour...",
    "sources": [
      { "source": "brian_balfour_retention.txt", "url": "", "excerpt": "..." }
    ],
    "artifact": null,
    "created_at": "2026-09-04T07:54:00Z"
  },
  "intent": "rag_answer"
}
```

---

## Component Boundaries

```
┌─────────────────────────────────────────────────────┐
│                    FastAPI App                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ /health  │  │/sessions │  │    /messages     │  │
│  └──────────┘  └──────────┘  └────────┬─────────┘  │
│                                        │             │
│                               ┌────────▼──────────┐ │
│                               │    Agent (router) │ │
│                               └────────┬──────────┘ │
│                    ┌───────────────────┼──────────┐  │
│                    ▼                   ▼          ▼  │
│             ┌──────────┐  ┌──────────────┐  ┌──────┐│
│             │RAG Answer│  │Ship30 Skill  │  │Artif.││
│             └────┬─────┘  └──────┬───────┘  └──┬───┘│
│                  │               │              │    │
│             ┌────▼───────────────▼──────────────▼──┐ │
│             │           LLM Client                 │ │
│             │  (Anthropic | OpenAI | Ollama)        │ │
│             └──────────────────────────────────────┘ │
│                                                       │
│  ┌─────────────────────┐  ┌──────────────────────┐   │
│  │   Knowledge Base    │  │   PostgreSQL (CRUD)  │   │
│  │  (FAISS Retriever)  │  │  sessions + messages │   │
│  └─────────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Ingestion / Retrieval Flow

1. **Load**: `retriever.py` scans `TRANSCRIPTS_DIR` for `.txt`, `.md`, and `.json` files
2. **Chunk**: Each file split into overlapping word-windows (`CHUNK_SIZE=800 words`, `CHUNK_OVERLAP=100 words`)
3. **Embed**: `sentence-transformers/all-MiniLM-L6-v2` encodes all chunks into 384-dim vectors (runs locally, no API key)
4. **Index**: FAISS `IndexFlatIP` (inner product = cosine on normalized vectors) stored at `VECTOR_INDEX_PATH`
5. **Retrieve**: On each query, top-K chunks selected by cosine similarity; index loaded from disk on restart
6. **Cite**: Each chunk carries its source filename; passed to LLM as context with citation instruction
7. **Refresh**: Re-run `build_index(force=True)` to pick up new transcript files

**Trade-off**: sentence-transformers + FAISS gives semantic retrieval (finds conceptually related chunks even without keyword overlap) at the cost of ~500 MB model download on first run. For a pure keyword demo, swap to TF-IDF by replacing the embed/index steps — retrieval quality will be lower but startup is instant.

---

## Agent Routing

The agent classifies each user message into one of three intents:

| Intent | Trigger keywords / pattern | Handler |
|---|---|---|
| `ship30` | "write essay", "ship 30", "ship30", "1250 words" | `ship30.py` skill |
| `artifact` | "create artifact", "generate html", "markdown doc", "render" | `artifact.py` skill |
| `rag_answer` | everything else | RAG retrieval + LLM answer |

Routing is keyword-based (no extra LLM call) to minimize latency and cost.

---

## Model Toggle

`LLM_PROVIDER` env var controls which client is instantiated at startup:

```python
# app/agent/llm_client.py
def get_llm_client(settings) -> BaseLLMClient:
    if settings.llm_provider == "anthropic":
        return AnthropicClient(settings)
    elif settings.llm_provider == "openai":
        return OpenAIClient(settings)
    else:
        return OllamaClient(settings)
```

All clients implement the same `complete(messages) -> str` interface. No application code changes needed to switch providers.

**Fallback behavior**: If Ollama is unavailable and `LLM_PROVIDER=ollama`, the health endpoint reports `ollama_available: false` and the message endpoint returns a 503 with a clear error message.

---

## Security

### Artifact Rendering
Generated HTML is rendered in a sandboxed iframe:
```html
<iframe sandbox="allow-same-origin" srcdoc="...user html..." />
```
- `allow-scripts` is **not** set → JavaScript is blocked
- `allow-forms` is **not** set → Form submission is blocked
- `allow-top-navigation` is **not** set → Cannot navigate parent frame
- Markdown is rendered via `react-markdown` which does not execute HTML by default

### API Security
- CORS restricted to `ALLOWED_ORIGINS`
- Input validated via Pydantic (max 10,000 chars per message)
- No secrets committed — `.env` is gitignored; `.env.example` has placeholder values

---

## Deployment Topology

```
Internet
    │
    ▼
┌─────────────────────────────────────────┐
│           Docker Compose Host           │
│                                         │
│  :3000  ┌──────────┐                   │
│  ──────► │ frontend │ (nginx)           │
│          └────┬─────┘                   │
│               │ /api/*                  │
│  :8000  ┌─────▼──────┐                 │
│  ──────► │  backend   │ (uvicorn)       │
│          └──┬──────┬──┘                 │
│             │      │                    │
│  :5432  ┌───▼──┐ ┌─▼──────┐            │
│         │  pg  │ │ ollama │ :11434      │
│         └──────┘ └────────┘            │
└─────────────────────────────────────────┘
```

For production deployment, replace Docker Compose with:
- Backend → AWS ECS / Railway / Fly.io
- Database → Supabase / RDS
- Frontend → Vercel / Netlify / S3+CloudFront
- Ollama → Keep local or use Anthropic/OpenAI cloud provider
