# System Architecture
**Project**: The Lenny Growth Assistant

## 1. High-Level Topology

The application follows a standard modern three-tier architecture:
1. **Frontend**: React (Vite) Single Page Application.
2. **Backend**: FastAPI (Python 3.13) providing RESTful JSON endpoints and Server-Sent Events (SSE) for streaming LLM generation.
3. **Database**: PostgreSQL (via Supabase) for transactional data (Users, Sessions, Messages, Artifacts, Citations).
4. **Vector Store**: Local ChromaDB for embedding storage and semantic retrieval.

## 2. Ingestion & Retrieval Flow (RAG)

### Ingestion
The raw podcast transcripts (Markdown files) are processed via `backend/scripts/ingest.py`:
1. **Chunking**: Transcripts are split into overlapping semantic chunks (800 characters, 100 character overlap) using LangChain's RecursiveCharacterTextSplitter.
2. **Indexing**: 
   - Each chunk is embedded using the `all-MiniLM-L6-v2` embedding model and stored in **ChromaDB**.
   - Simultaneously, each chunk is tokenized and indexed into a fast in-memory **BM25 (Rank-BM25)** index.

### Retrieval
When a user asks a question:
1. The query is embedded and searched against ChromaDB (Semantic Search).
2. The query is tokenized and searched against the BM25 index (Lexical/Keyword Search).
3. The results from both lists are merged and re-ranked using **Reciprocal Rank Fusion (RRF)**.
4. The top *k* chunks are formatted into a `<transcript_sources>` XML block and injected into the LLM prompt.

## 3. Agent Routing & Model Toggle

The system fulfills the assignment requirement to support both Cloud and Local LLMs seamlessly:
- **`app/agent/router.py`**: The `get_agent()` factory function acts as the routing layer. 
- When a user submits a query, the router checks the `user` object in the database.
- If the user has provided a valid `CLAUDE_API_KEY`, the router instantiates the `ClaudeAgent` (using the official Anthropic SDK).
- If the user does *not* have a key, or if the environment forces local mode, the router seamlessly instantiates the `OllamaAgent` (communicating with the local `llama3.2:latest` model on port `11434`).
- This abstraction ensures the main application logic (`chat.py`) remains completely ignorant of the underlying model provider.

## 4. Database Schema (PostgreSQL)

The relational data is managed via SQLAlchemy ORM (Async).

- **Users**: `id`, `username`, `hashed_password`, `claude_api_key`.
- **Sessions**: `id`, `user_id`, `title`, `model_provider`, `model_name`, `created_at`.
- **Messages**: `id`, `session_id`, `role` ("user" | "assistant"), `content`, `created_at`.
- **Artifacts**: `id`, `message_id`, `artifact_type` ("markdown" | "html"), `title`, `content`.
- **Citations**: `id`, `message_id`, `episode_title`, `guest`, `chunk_text`, `relevance_score`.

## 5. Security & Isolation

### Artifact Rendering (Untrusted HTML)
The LLM can generate arbitrary HTML and JavaScript via the Artifact skill. To prevent Cross-Site Scripting (XSS) and data leakage:
- The Artifact Viewer renders HTML via a sandboxed `<iframe>`.
- The `sandbox` attribute is explicitly set to `"allow-scripts"`.
- **Crucially, we OMIT `allow-same-origin`**. This forces the iframe into a unique origin. Any JavaScript executing inside the iframe cannot access the parent window's DOM, cannot read cookies, and cannot make authenticated requests to our API.

## 6. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create a new user account. |
| `POST` | `/auth/token` | Authenticate and receive a JWT. |
| `GET` | `/auth/me` | Fetch current user profile and settings. |
| `GET` | `/sessions` | List all conversation sessions for the user. |
| `POST` | `/sessions` | Create a new conversation session. |
| `GET` | `/sessions/{id}/messages` | Fetch history for a session (including Artifacts/Citations). |
| `POST` | `/chat/stream` | Send a message. Returns Server-Sent Events (SSE) stream. |
