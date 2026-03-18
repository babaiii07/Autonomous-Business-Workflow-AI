# Autonomous Business Workflow AI (AI COO)

Production-grade, modular **Autonomous Business Workflow AI** built with **LangGraph + LangChain**, **Groq** for LLM inference, **Pinecone** for long-term memory (RAG), **Tavily** for external search, **FastAPI** backend APIs, **PostgreSQL/SQLite** structured storage, and a **Streamlit** dashboard.

## What this does

Email Input → Parsing → Invoice Extraction → Memory Retrieval → Financial Analysis → Decision → Human Approval (if needed) → Action → Memory Update

## Project structure

```text
agents/        LangChain agent factories + prompts
tools/         External integrations (email, DB, Tavily, Pinecone)
workflows/     LangGraph workflow graph + state
memory/        Vector memory abstractions + Pinecone adapter
api/           FastAPI app (workflow endpoints + approvals)
frontend/      Streamlit dashboard
config/        Settings + env loading
utils/         Logging, retries, helpers
```

## Quickstart (Docker)

1. Copy env template:

```bash
cp .env.example .env
```

2. Start services:

```bash
docker compose up --build
```

- FastAPI: `http://localhost:8000/docs`
- Streamlit: `http://localhost:8501`

## Local dev (no Docker)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0
```

## Notes

- **No secrets are hardcoded**. All integrations are configured via environment variables.
- Pinecone/Groq/Tavily are optional for local smoke tests; the system falls back to safe no-op adapters when keys are missing.

