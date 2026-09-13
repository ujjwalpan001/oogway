# PRD: The Lenny Growth Assistant

**Version:** 1.0  
**Author:** Forward Deployed Engineer Candidate  
**Date:** September 2026

---

## 1. Forward Deployment Brief

### User and Problem

**Primary user:** A product manager or growth practitioner who regularly listens to Lenny's Podcast. They already trust Lenny's content but currently can't search or query it efficiently. When preparing for a strategy review, writing a think-piece, or evaluating a growth idea, they need to pull the best relevant advice from 269 episodes without spending hours searching YouTube transcripts manually.

**Job-to-be-done:** Get grounded, source-cited answers to specific product and growth questions in under 60 seconds — and optionally turn those answers into shareable written content without needing to write from scratch.

**Pain removed:** The assistant removes three distinct pains:
1. *Search friction* — no more manually hunting through transcripts or YouTube
2. *Trust gap* — every answer cites the exact episode, guest, and timestamp, so users can verify
3. *Output gap* — instead of copying Lenny quotes into a doc and rearranging them, users get a finished essay or report in one click

### Success Metric

**Primary metric:** Answer grounding rate — the percentage of assistant responses that include at least one valid source citation from the transcript corpus. Target: >95%.

**Secondary metric:** Time-to-answer — users get a cited answer in <15 seconds on Groq, <60 seconds on local Ollama.

**Evaluator metric (for this submission):** Can a fresh evaluator clone, run, and get a grounded answer within 10 minutes of reading the README?

### Assumptions

1. The client team runs on macOS or Linux for production; Windows for development (this submission).
2. The 269-transcript corpus is refreshed manually (a re-ingest script is provided). Real-time sync from Lenny's YouTube was out of scope.
3. Users are internal — there is no authentication/login. This is explicitly noted as a risk.
4. The evaluator has a Groq API key (free) OR Ollama installed locally. The demo defaults to Groq.
5. "Grounded" means the LLM receives retrieved transcript chunks and is instructed not to go beyond them. Hallucinations are possible but bounded.
6. DOMPurify + sandboxed iframe is sufficient HTML isolation for a trusted-user internal tool.

### Scope Choices

**Included:**
- Multi-session chat with full history persistence
- Hybrid BM25 + semantic retrieval with source citations
- Ship 30 for 30 essay skill (encoded, not a one-off prompt)
- HTML + Markdown artifact generation with in-app viewer
- Groq + Ollama model toggle (no code changes required)
- Docker Compose one-command startup
- Structured logging with request IDs
- Automated test suite

**Excluded:**
- User authentication (no login screen)
- Automatic transcript refresh / webhook from YouTube
- Mobile-specific layout (responsive down to 768px, not 375px)
- Streaming token-by-token to the artifact viewer (artifacts are generated in one call)
- RAG evaluation framework (relevance scoring is approximate RRF score, not RAGAS)

### Risks and Trade-offs

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Hallucination beyond transcript corpus | Medium | High | System prompt strictly forbids going beyond provided context; citations show the source |
| Ollama quality on small models | High | Medium | llama3.2:3b is sufficient for RAG; users can switch to llama3:8b |
| Groq rate limits (free tier) | Low | Medium | Errors surfaced in UI with clear message; falls back gracefully |
| HTML artifact XSS | Low | Low | `sandbox="allow-scripts"` without `allow-same-origin` creates null origin; plus DOMPurify pre-pass |
| Ingestion time (269 episodes) | Medium | Low | One-time, skips already-ingested chunks; progress logged |
| Database connection pool exhaustion | Low | Medium | Pool pre-ping, pool_size=5, max_overflow=10; health endpoint monitors |

---

## 2. Product Flows

### Core Chat Flow

1. User opens the app → sees empty state with 4 suggested questions
2. User types a question or clicks a suggestion
3. App creates a session (auto, on first message)
4. Backend retrieves top-5 transcript chunks via hybrid search
5. Agent streams a grounded response with inline citations
6. Citations appear as collapsible cards below the message
7. If an artifact was generated, a preview card appears; click opens the viewer

### Ship 30 Essay Flow

1. User selects "Ship 30 Essay" from the skill selector (or types "write a Ship 30 essay about...")
2. Backend detects skill intent (explicit or keyword-based)
3. Ship30 skill runs with the 10-principle system prompt
4. Essay appears in the chat AND as a Markdown artifact in the viewer
5. User can copy or download the .md file

### Artifact Generation Flow

1. User selects "HTML Report" or "Markdown Doc" from skill selector
2. Backend generates self-contained document
3. Artifact viewer slides in with rendered preview
4. Toggle to "Code" view to see raw content
5. Security note shown at bottom: "Rendered in sandboxed iframe · External network access blocked"

### Model Toggle Flow

1. User opens `.env`, changes `LLM_PROVIDER=groq` → `LLM_PROVIDER=ollama`
2. Restarts backend (`uvicorn app.main:app --reload`)
3. Badge in top-right updates to show Ollama + model name
4. Full feature parity maintained

---

## 3. Acceptance Criteria

| # | Feature | Criteria |
|---|---------|---------|
| 1 | Session creation | POST /sessions returns 201 with valid session ID |
| 2 | Grounded chat | Every assistant response includes ≥1 citation when transcript content exists |
| 3 | Multi-turn context | Follow-up questions resolve correctly using prior 10 messages |
| 4 | Ship 30 skill | Essay output is ~1,200-1,300 words, has headings, bold, and a specific takeaway |
| 5 | Artifact viewer | HTML renders in sandboxed iframe; Markdown renders with proper styling |
| 6 | Model toggle | Switching LLM_PROVIDER works without code changes |
| 7 | Health endpoint | Returns per-component status for DB, ChromaDB, and LLM |
| 8 | Empty retrieval | When no relevant chunks found, assistant says so clearly (no hallucination) |
| 9 | Streaming | Tokens stream progressively; stop button cancels generation |
| 10 | Docker | `docker-compose up --build` starts all services; ingestion script runs inside container |
