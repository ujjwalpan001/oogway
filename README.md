# The Lenny Growth Assistant

> An AI assistant grounded in 269 Lenny's Podcast transcripts — answers product and growth questions, writes Ship 30 essays, and generates renderable artifacts.

![Architecture](docs/architecture-diagram.png)

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running Locally (Dev)](#running-locally-dev)
- [Running with Docker Compose](#running-with-docker-compose)
- [Ingesting Transcripts](#ingesting-transcripts)
- [Running Tests](#running-tests)
- [Model Configuration](#model-configuration)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

---

## Architecture Overview

```
Frontend (React + Vite)  →  FastAPI Backend  →  PostgreSQL
                              ↓
                         Hybrid Retriever (BM25 + ChromaDB)
                              ↓
                         Agent Router (Groq | Ollama)
                              ↓
                         Skills (Ship30 | Artifact Gen)
```

Full details in [`architecture.md`](architecture.md).

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.11+ | [python.org](https://python.org) |
| Node.js | 20+ | [nodejs.org](https://nodejs.org) |
| Docker + Compose | v2+ | [docker.com](https://docker.com) |
| Git | any | [git-scm.com](https://git-scm.com) |
| Ollama *(for local LLM)* | latest | [ollama.com](https://ollama.com) |

---

## Installation

```bash
# 1. Clone this repo
git clone https://github.com/your-username/lenny-growth-assistant.git
cd lenny-growth-assistant

# 2. Clone the transcripts into data/transcripts
git clone https://github.com/ChatPRD/lennys-podcast-transcripts.git data/transcripts

# 3. Copy and fill in .env
cp .env.example .env
# Edit .env — add your GROQ_API_KEY (get one free at console.groq.com)
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | Yes | `groq` | `groq` or `ollama` |
| `GROQ_API_KEY` | If using Groq | — | From [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | No | `llama3-70b-8192` | Any Groq model name |
| `OLLAMA_BASE_URL` | If using Ollama | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | If using Ollama | `llama3.2:3b` | Run `ollama pull llama3.2:3b` first |
| `DATABASE_URL` | No | SQLite fallback | PostgreSQL connection string |
| `RETRIEVAL_TOP_K` | No | `5` | Number of chunks to retrieve |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## Running Locally (Dev)

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens on http://localhost:3000
```

### Ingest Transcripts (one-time)

```bash
cd backend
python scripts/ingest.py
# This takes 5-15 minutes for all 269 episodes
# Safe to re-run — skips already-ingested chunks
```

---

## Running with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# App available at:
#   Frontend: http://localhost:3000
#   Backend API: http://localhost:8000
#   API Docs: http://localhost:8000/docs

# Ingest transcripts (first run only)
docker-compose exec backend python scripts/ingest.py
```

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pip install aiosqlite  # needed for in-memory test DB

pytest tests/ -v
```

Expected output:
```
tests/test_api.py ......... PASSED
tests/test_retrieval.py ....... PASSED
tests/test_skills.py ...... PASSED
```

---

## Model Configuration

### Switching to Ollama (local, no API key)

1. [Install Ollama](https://ollama.com/download)
2. Pull a model: `ollama pull llama3.2:3b`
3. Start Ollama: `ollama serve`
4. In `.env`:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2:3b
   ```
5. Restart the backend

### Switching to Groq (cloud, fast)

1. Get a free API key at [console.groq.com](https://console.groq.com)
2. In `.env`:
   ```
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_...
   GROQ_MODEL=llama3-70b-8192
   ```

The UI shows the active provider in the top-right badge.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Ollama not reachable` | Run `ollama serve` and check `OLLAMA_BASE_URL` |
| `GROQ_API_KEY not set` | Add key to `.env`, restart backend |
| Empty answers / "no relevant excerpts" | Run `python scripts/ingest.py` first |
| DB connection error | Check `DATABASE_URL` or let Docker Compose provision PostgreSQL |
| Frontend can't reach backend | Check CORS_ORIGINS in config, verify backend is on port 8000 |
| Streaming stops midway | Nginx proxy buffering — ensure `proxy_buffering off` in nginx.conf |

---

## Project Structure

```
lenny-growth-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, middleware
│   │   ├── config.py        # Settings from .env
│   │   ├── database.py      # SQLAlchemy async
│   │   ├── models.py        # DB models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── routers/         # API routes
│   │   ├── agent/           # LLM agents + skills
│   │   └── rag/             # Retrieval pipeline
│   ├── scripts/ingest.py    # One-time ingestion
│   └── tests/               # Pytest test suite
├── frontend/
│   └── src/
│       ├── components/      # React components
│       ├── hooks/           # useChat, useSession
│       └── lib/api.ts       # API client
├── data/transcripts/        # 269 episode transcripts (git cloned)
├── docker-compose.yml
├── .env.example
├── README.md
├── PRD.md
├── design.md
└── architecture.md
```
