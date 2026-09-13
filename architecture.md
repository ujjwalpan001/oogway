# Architecture: The Lenny Growth Assistant

---

## System Topology

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser (React + Vite)                    │
│                                                             │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │  Session Sidebar │  │  Chat Panel + Input              │  │
│  │  (session list) │  │  (SSE streaming, skill selector) │  │
│  └─────────────────┘  └──────────────────────────────────┘  │
│                        ┌──────────────────────────────────┐  │
│                        │  Artifact Viewer (sandboxed)     │  │
│                        └──────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP + SSE (proxied via Nginx)
┌─────────────────────────────▼───────────────────────────────┐
│                   FastAPI Backend (Python 3.11)              │
│                                                             │
│  Middleware: RequestID · CORS · GlobalExceptionHandler      │
│                                                             │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌─────────────┐  │
│  │ /health  │ │ /sessions  │ │ /chat    │ │   /docs     │  │
│  │          │ │ CRUD       │ │ /stream  │ │  (OpenAPI)  │  │
│  └──────────┘ └────────────┘ └─────┬────┘ └─────────────┘  │
│                                    │                        │
│  ┌─────────────────────────────────▼────────────────────┐   │
│  │              Agent Router (reads LLM_PROVIDER)       │   │
│  │                                                      │   │
│  │  ┌─────────────────┐    ┌──────────────────────┐    │   │
│  │  │   GroqAgent      │    │   OllamaAgent         │    │   │
│  │  │   (cloud, fast)  │    │   (local, private)    │    │   │
│  │  └─────────────────┘    └──────────────────────┘    │   │
│  │                                                      │   │
│  │  Skills: ship30.py · artifact_gen.py                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              HybridRetriever                         │    │
│  │  BM25 (rank_bm25) + ChromaDB (sentence-transformers) │    │
│  │  Reciprocal Rank Fusion → top-5 chunks               │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌───────────────────┐                                      │
│  │ structlog (JSON)  │ ← request_id bound to every line     │
│  └───────────────────┘                                      │
└─────────────────────────────┬───────────────────────────────┘
                    ┌─────────┴──────────┐
          ┌─────────▼──────┐   ┌─────────▼───────┐
          │  PostgreSQL 16  │   │  ChromaDB        │
          │  (sessions,     │   │  (embeddings,    │
          │   messages,     │   │   transcript     │
          │   artifacts,    │   │   chunks)        │
          │   citations)    │   └─────────────────┘
          └────────────────┘
```

---

## Database Schema

```sql
CREATE TABLE sessions (
  id            VARCHAR(36)  PRIMARY KEY,
  title         VARCHAR(255) NOT NULL DEFAULT 'New conversation',
  model_provider VARCHAR(50) NOT NULL,
  model_name    VARCHAR(100) NOT NULL,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE messages (
  id         VARCHAR(36)  PRIMARY KEY,
  session_id VARCHAR(36)  REFERENCES sessions(id) ON DELETE CASCADE,
  role       VARCHAR(20)  NOT NULL CHECK (role IN ('user', 'assistant')),
  content    TEXT         NOT NULL,
  created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE artifacts (
  id            VARCHAR(36)  PRIMARY KEY,
  message_id    VARCHAR(36)  REFERENCES messages(id) ON DELETE CASCADE,
  artifact_type VARCHAR(20)  NOT NULL,
  title         VARCHAR(255) NOT NULL DEFAULT '',
  content       TEXT         NOT NULL,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE citations (
  id              VARCHAR(36)  PRIMARY KEY,
  message_id      VARCHAR(36)  REFERENCES messages(id) ON DELETE CASCADE,
  episode_title   VARCHAR(500) DEFAULT '',
  guest           VARCHAR(255) DEFAULT '',
  chunk_text      TEXT         DEFAULT '',
  youtube_url     VARCHAR(500) DEFAULT '',
  relevance_score INTEGER      DEFAULT 0
);
```

---

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | DB + ChromaDB + LLM status | None |
| POST | `/sessions` | Create new session | None |
| GET | `/sessions` | List all sessions | None |
| GET | `/sessions/{id}` | Get session with messages | None |
| DELETE | `/sessions/{id}` | Delete session and history | None |
| POST | `/chat/stream` | Stream chat response (SSE) | None |
| GET | `/docs` | OpenAPI documentation | None |

### Chat SSE Event Types

```
data: {"type": "skill_start", "skill": "ship30"}
data: {"type": "token", "content": "..."}
data: {"type": "done", "message_id": "...", "citations": [...], "artifact": {...}}
data: {"type": "error", "message": "..."}
```

---

## Ingestion and Retrieval Flow

```
data/transcripts/{guest}/transcript.md
         ↓
  1. Parse YAML frontmatter (guest, title, youtube_url, date)
  2. Extract body text
  3. Chunk at 800 words / 100-word overlap
  4. Embed with all-MiniLM-L6-v2 (SentenceTransformer)
  5. Store in ChromaDB with episode metadata
  6. Build BM25 index from same corpus (in-memory, rebuilt on startup)

Query time:
  → Semantic search (ChromaDB, cosine similarity) → top-10
  → Keyword search (BM25Okapi) → top-10
  → Reciprocal Rank Fusion (k=60) → deduplicated, ranked top-5
  → Format as [Source N: Guest — "Episode Title"] + chunk text
  → Inject into LLM system context
```

---

## Agent Routing

```python
settings.llm_provider  →  "groq" | "ollama"
                               ↓
                    get_agent() singleton
                               ↓
              GroqAgent | OllamaAgent  (both implement BaseAgent)
                               ↓
            .stream() or .complete()  (async generators)
```

Skill detection runs before the agent call:
```python
"ship 30 essay" in message  →  ship30 skill
"html report" in message    →  artifact:html skill
else                        →  standard grounded chat
```

---

## Artifact Security Model

HTML artifacts could potentially run malicious JavaScript if an attacker controls the LLM output.

**Defense layers:**

1. **DOMPurify pre-pass**: Strips dangerous HTML attributes (`onerror`, `onclick`, etc.) and disallowed tags before the content reaches the iframe.

2. **Null-origin sandbox**: The iframe uses `sandbox="allow-scripts"` WITHOUT `allow-same-origin`. This forces the iframe into a null origin, which means:
   - Cannot access `window.parent`
   - Cannot read cookies or localStorage from the parent page
   - Cannot make credentialed fetch requests to the parent origin
   - Cannot navigate the parent frame

3. **No external network**: Content is rendered from a blob URL or written via `document.write()`, not served as a real URL, so no external images or scripts are loaded.

4. **What is permitted**: The artifact can run inline JavaScript and render CSS. This is intentional — otherwise HTML reports with charts or interactive tables wouldn't work.

**Acceptable risk**: For an internal single-user tool, this level of isolation is appropriate. For multi-user or public deployment, server-side HTML sanitization (via a headless browser or a strict allowlist) would be required.

---

## Model Toggle Implementation

```
.env: LLM_PROVIDER=groq|ollama
         ↓
config.py: Settings(llm_provider=...)
         ↓
agent/router.py: get_agent() checks settings.llm_provider
         ↓
Returns GroqAgent or OllamaAgent (both implement BaseAgent)
```

Fallback behavior:
- If Groq API key is missing: `GroqAgent.is_available()` returns False; `/health` shows `"llm": "unavailable"`
- If Ollama is not running: `OllamaAgent.stream()` raises `RuntimeError` with a clear message; UI displays the error inline

---

## Deployment Topology

```
Docker Compose (local):
  - postgres:16-alpine (port 5432)
  - backend: FastAPI (port 8000)
  - frontend: Nginx serving Vite bundle (port 3000)
    → /api/* proxied to backend:8000

External (optional):
  - Supabase as managed PostgreSQL
  - Railway / Fly.io for backend
  - Vercel / Cloudflare Pages for frontend
```

Volumes:
- `postgres_data` — persists database across container restarts
- `chroma_data` — persists embeddings so ingestion doesn't re-run
