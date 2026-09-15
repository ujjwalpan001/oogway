# Product Requirements Document (PRD)
**Project**: The Lenny Growth Assistant
**Author**: Forward Deployed Engineer Candidate

## 1. User & Problem

**Primary User**: 
Product Managers and Growth team members who need to quickly reference, synthesize, or share insights from Lenny's Podcast transcripts.

**Problem Job to be Done (JTBD)**:
"When I am researching a growth tactic or product strategy, I want to quickly pull relevant, accurate insights from industry leaders featured on Lenny's Podcast, so that I can apply their proven methodologies without spending hours listening to or reading through hundreds of raw transcripts."

**Pain Relieved**:
The current process requires manual keyword searching through raw text files or relying on generalized AI models (like ChatGPT) that hallucinate quotes and cannot cite specific episodes. 

## 2. Success Metrics

1. **Operational Efficiency**: Reduce time to find a specific framework or quote from >15 minutes (manual search) to <10 seconds.
2. **Quality Metric (Grounding)**: 0% hallucinated quotes. 100% of claims must have an attached, verifiable citation from the knowledge base.

## 3. Assumptions

Due to the ambiguous nature of the prompt, the following assumptions were made:
- **Single-Tenant Use Case**: The assistant is an internal tool. Complex RBAC (Role-Based Access Control) or multi-tenant data isolation is not required for this phase. 
- **Offline/Local Preference**: The team highly values data privacy, hence the mandatory requirement to support local models (Ollama).
- **Transcript Format**: The raw data consists of markdown transcripts. The system assumes a directory structure of `.md` files containing guest names and dialogue.

## 4. Scope Choices

### In Scope
- **Hybrid Retrieval (BM25 + ChromaDB)**: We chose to implement both lexical (BM25) and semantic search. Semantic search alone struggles with exact-match queries like "What did Brian Chesky say about design?", while BM25 excels at it.
- **Dynamic Model Fallback**: If a Claude API key is missing, the system seamlessly falls back to a local Ollama model (`llama3.2:latest`) to guarantee operational readiness.
- **Artifact Viewer**: A dedicated, isolated iframe viewer to render generated HTML/Markdown without redirecting the user.
- **Ship 30 for 30 Skill**: A strict system prompt designed to enforce the hook/problem/credibility/takeaway structure of Ship 30 essays.

### Out of Scope (Intentional)
- **OAuth / SSO**: Complex auth flows were excluded in favor of a minimal, fast "session ownership" model using a simple login screen.
- **Alembic Migrations**: For an evaluator to quickly spin up the project, `SQLAlchemy.metadata.create_all()` is used. Managing migration state locally on evaluator machines often causes friction.

## 5. Risks & Trade-offs

| Risk Area | Description | Mitigation Strategy |
|-----------|-------------|---------------------|
| **Hallucination** | LLMs naturally invent quotes when unsure. | Enforced strict `CHAT_SYSTEM` prompts requiring the model to say "I don't know" if the context chunks are empty. |
| **Artifact Security** | Generated HTML could execute malicious JS. | The Artifact Viewer uses an `<iframe>` with `sandbox="allow-scripts"`. By omitting `allow-same-origin`, the iframe is forced into a unique origin, completely isolated from the parent application state and cookies. |
| **Latency (Local)** | Local models via Ollama are significantly slower than cloud APIs. | The frontend uses streaming UI components. The immediate token streaming reduces perceived latency for the user. |
| **Port Conflicts** | The user's environment might block standard Postgres ports. | The backend uses Supabase Postgres by default to bypass local Docker/Port setup friction, with local Docker Compose provided as a fallback. |
