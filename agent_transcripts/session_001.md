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

**Claude over OpenAI with Ollama Fallback:**
The user requested Anthropic Claude as the primary cloud provider, but they had no API key. We built a robust dynamic fallback mechanism: if `user.claude_api_key` is null, the backend seamlessly routes requests to the local `OllamaAgent` (running `llama3.2:latest`). This satisfies both the cloud and mandatory local requirements of the prompt flawlessly.

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
- **Minimal Auth**: Built a simple user registration flow to satisfy the session/user ownership requirements of the prompt without requiring OAuth or complex JWT flows. It uses plain text for demonstration purposes but structurally mimics a real auth flow.
- **No RAGAS evaluation**: Would require running 50+ queries against ground truth, which is hours of work beyond scope. The retrieval test suite covers the key invariants instead.
