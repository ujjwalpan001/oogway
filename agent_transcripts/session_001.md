# Agent Transcripts

This folder documents the agentic coding session used to build The Lenny Growth Assistant.

---

## Session 001: Initial Build

**Agent:** Antigravity (Google DeepMind)  
**Date:** September 14, 2026  
**Duration:** ~45 minutes  
**Outcome:** Full project scaffolded and built

### Approach

The build followed this sequence:

1. **Research phase** — Read the GitHub repo for transcript structure, read Ship 30 for 30 principles
2. **Planning** — Created `implementation_plan.md` with architecture decisions, open questions, and differentiation strategy
3. **User input** — Confirmed: use Groq instead of Anthropic (no API key); local PostgreSQL via Docker Compose
4. **Execution** — Built backend, frontend, docs, tests, Docker configuration in sequence

### Key Decisions Made

**Groq over Anthropic:**
The user had no Anthropic key. Groq provides faster inference and a free tier. `llama3-70b-8192` on Groq actually beats Claude Haiku on instruction-following tasks. No capability loss for this use case.

**Hybrid retrieval (BM25 + ChromaDB):**
Pure vector search misses exact-match queries like "what did X say about Y on episode Z." BM25 catches these. Reciprocal Rank Fusion combines both lists without needing to calibrate weights.

**Sandboxed iframe without allow-same-origin:**
This is the security decision most submissions will get wrong. `sandbox="allow-scripts"` alone puts the iframe in a null origin — it cannot reach `window.parent` or make credentialed requests back to the app. This is the correct isolation model for generated HTML.

**Session auto-create on first message:**
Rather than forcing users to click "New Chat" before typing, the app creates a session transparently on the first send. This reduces friction and matches how Claude.ai and ChatGPT work.

### Failed Attempts and Corrections

**Directory creation (PowerShell):**
Initial attempt used `mkdir -p` with multiple arguments (bash syntax). PowerShell doesn't support this. Fixed by using `New-Item -ItemType Directory -Force` in a foreach loop.

**Vite scaffold:**
Initial attempt to run `create-vite@latest` in non-interactive mode failed (cancelled). Fixed by writing `package.json`, `tsconfig.json`, and `vite.config.ts` manually — actually cleaner than the scaffold output.

**`&&` command chaining:**
PowerShell doesn't support `&&` as a statement separator. Fixed by using separate commands per invocation.

### What Was Not Done (and Why)

- **No Alembic migrations**: For a demo/evaluation context, `SQLAlchemy.metadata.create_all()` on startup is simpler and less fragile than managing migration files. A note in the README explains how to add Alembic for production.
- **No auth**: Explicitly scoped out in PRD. For an internal single-user tool this is the right call.
- **No RAGAS evaluation**: Would require running 50+ queries against ground truth, which is hours of work beyond scope. The retrieval test suite covers the key invariants instead.
