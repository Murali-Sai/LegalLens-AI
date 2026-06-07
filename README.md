# LegalLens — AI-Powered Legal Document Analyst

![CI](https://github.com/Murali-Sai/LegalLens-AI/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

An agentic AI system that analyzes legal contracts, identifies risky clauses, and generates plain-English explanations with recommended actions — built with LangGraph, RAG, and the Claude API.

> **Disclaimer:** This tool provides informational analysis only — not legal advice.

---

## The Problem

Millions of people sign contracts they don't fully understand. Legal review costs $300–500/hour, putting it out of reach for most individuals and small businesses. LegalLens democratizes contract understanding through a multi-step AI reasoning pipeline.

---

## Architecture

```
Upload (PDF / DOCX)
        │
        ▼
┌─────────────┐    SSE progress    ┌─────────────────────────────┐
│  FastAPI    │ ──────────────────▶│  React + Tailwind CSS       │
│  Backend    │◀── file upload ─── │  Frontend                   │
└──────┬──────┘                    └─────────────────────────────┘
       │
       ▼  LangGraph StateGraph
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  1. EXTRACT │──▶│  2. ANALYZE │──▶│  3. COMPARE │
│ Unstructured│   │  Claude API │   │  ChromaDB   │
└─────────────┘   └─────────────┘   └──────┬──────┘
                                           │
                  ┌─────────────┐   ┌──────▼──────┐
                  │  5. EXPLAIN │◀──│   4. FLAG   │
                  │  Claude API │   │  Claude API │
                  └──────┬──────┘   └─────────────┘
                         │
                         ▼
               Risk Dashboard + Actions
               (persisted to SQLite)
```

**5-step LangGraph pipeline:**

| Step | What happens |
|------|-------------|
| **Extract** | Parse PDF/DOCX into text chunks via Unstructured.io (PyMuPDF fallback) |
| **Analyze** | Claude classifies each chunk into one of 9 clause types |
| **Compare** | ChromaDB RAG benchmarks each clause against a curated standard/risky clause database |
| **Flag** | Claude scores risk level (low / medium / high) with 2–3 sentence reasoning |
| **Explain** | Claude generates a plain-English summary + single recommended action per clause |

The frontend receives **real-time step updates** via Server-Sent Events (SSE) — no fake progress timers.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | LangGraph (multi-step agentic pipeline) |
| LLM | Claude API (Anthropic) — auto-falls back to keyword analysis if no key |
| RAG | ChromaDB + sentence-transformers |
| Doc Parsing | Unstructured.io (PyMuPDF fallback) |
| Backend | FastAPI + SSE streaming |
| Persistence | SQLite (analysis history survives restarts) |
| Frontend | React 18 + Tailwind CSS + Vite |
| Evaluation | MLflow (precision/recall/F1, MRR@5, risk accuracy) |
| CI/CD | GitHub Actions (lint → test → build → GCP Cloud Run deploy) |
| Deployment | Render (backend + frontend) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Anthropic API key ([get one here](https://console.anthropic.com))

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install ".[dev]"
cp .env.example .env        # Edit and add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

> **No API key?** Set `MOCK_MODE=true` in `.env` to run keyword-based analysis instantly.

### Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### Docker Compose (both services)
```bash
docker compose up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check + mock mode status |
| `POST` | `/api/upload-stream` | Upload doc → SSE stream of step progress + final result |
| `GET` | `/api/demo-stream` | SSE stream using bundled sample contract |
| `POST` | `/api/upload` | Synchronous upload (returns full result, no streaming) |
| `GET` | `/api/analysis/{id}` | Retrieve a saved analysis |
| `GET` | `/api/analyses` | List all past analyses (newest first) |
| `GET` | `/api/stats` | Aggregate stats across all analyses |
| `POST` | `/api/evaluate` | Log evaluation metrics to MLflow |
| `POST` | `/api/evaluate/run` | Run automated eval against ground truth |

### SSE Stream Format (`/api/upload-stream`)

```
event: progress
data: {"step": "extract", "step_index": 0}

event: progress
data: {"step": "analyze", "step_index": 1}

... (compare, flag, explain)

event: complete
data: { <full AnalysisResult JSON> }
```

---

## Deployment on Render

1. Fork this repo and connect it to [Render](https://render.com)
2. Render auto-detects `render.yaml` and creates both services
3. In the Render dashboard → `legallens-backend` → **Environment**, add:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```
4. Deploy — the frontend auto-proxies `/api` to the backend

The backend mounts a **1 GB persistent disk** at `/data` for ChromaDB and SQLite.

> **Plan note:** The backend needs at least **2 GB RAM** for sentence-transformers (ChromaDB embeddings). Use the **Standard** plan ($25/month). The frontend runs on the **Free** plan.

---

## Evaluation

MLflow tracks:
- **Clause detection**: macro precision, recall, F1 per clause type
- **Retrieval quality**: MRR@5, hit rate against ChromaDB
- **Risk scoring**: accuracy + agreement rate vs. 30 expert-labeled samples
- **E2E latency**: seconds per document, seconds per clause

Run manually:
```bash
cd backend
python -m app.evaluation.runner                  # all tasks
python -m app.evaluation.runner --task clause    # clause detection only
python -m app.evaluation.runner --task risk      # risk scoring only
```

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes.py       # FastAPI endpoints + SSE streaming
│   │   ├── core/               # Config (pydantic-settings), Pydantic models
│   │   ├── db.py               # SQLite persistence (analysis history)
│   │   ├── pipeline/           # LangGraph graph, nodes, prompts, mock
│   │   ├── rag/                # ChromaDB vector store + seed data ingest
│   │   └── evaluation/         # MLflow tracking + automated eval runner
│   ├── data/
│   │   ├── clause_database/    # Seed JSON (standard + risky clauses)
│   │   ├── evaluation/         # 30-sample ground truth dataset
│   │   └── sample_contracts/   # Bundled demo contract
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   └── utils/api.js        # SSE streaming client + REST helpers
│   ├── nginx.conf              # Reverse proxy + SSE buffering disabled
│   └── Dockerfile              # Multi-stage build → nginx
├── .github/workflows/ci.yml    # Lint → Test → Build → GCP Cloud Run
├── render.yaml                 # Render deployment config
└── docker-compose.yml
```

---

## License

MIT
