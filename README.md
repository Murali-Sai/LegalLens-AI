# LegalLens — AI-Powered Legal Document Analyst Agent

An agentic AI system that analyzes legal contracts, identifies risky clauses, and generates plain-English explanations with recommended actions. Built with LangGraph, RAG pipelines, and Claude API.

> **Disclaimer:** This tool provides informational analysis only — not legal advice.

## Problem

Millions of people sign contracts they don't fully understand. Legal review costs $300–500/hour, putting it out of reach for most individuals and small businesses. LegalLens democratizes contract understanding through AI-powered multi-step reasoning.

## Architecture

```
  Upload (PDF/DOCX)
         │
         ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   EXTRACT   │────▶│   ANALYZE   │────▶│   COMPARE   │
  │ Unstructured│     │  Claude API  │     │ ChromaDB RAG│
  └─────────────┘     └─────────────┘     └──────┬──────┘
                                                  │
                      ┌─────────────┐     ┌──────▼──────┐
                      │   EXPLAIN   │◀────│    FLAG     │
                      │  Claude API  │     │  Claude API  │
                      └──────┬──────┘     └─────────────┘
                             │
                             ▼
                   Risk Dashboard + Actions
```

**5-Step LangGraph Pipeline:**
1. **Extract** — Parse PDF/DOCX into structured text chunks
2. **Analyze** — Classify clause types (liability, termination, IP, payment, confidentiality)
3. **Compare** — Benchmark against standard clauses via RAG retrieval
4. **Flag** — Score risk level (low/medium/high) with reasoning
5. **Explain** — Generate plain-English summaries and recommended actions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Orchestration | LangGraph (multi-step agentic pipeline) |
| LLM | Claude API (Anthropic) |
| RAG | ChromaDB + sentence-transformers |
| Doc Parsing | Unstructured.io |
| Backend | FastAPI |
| Frontend | React + Tailwind CSS |
| Evaluation | MLflow |
| Infrastructure | Docker, GitHub Actions CI/CD, GCP Cloud Run |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Anthropic API key

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install ".[dev]"
cp .env.example .env  # Add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/upload` | Upload and analyze a document |
| GET | `/api/analysis/{id}` | Retrieve analysis results |

## Evaluation

MLflow tracks:
- **Clause detection**: precision, recall, F1 across 5+ clause types
- **Retrieval quality**: MRR@5, hit rate
- **Risk scoring**: agreement rate with expert labels
- **End-to-end latency**: processing time per document

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, Pydantic models
│   │   ├── pipeline/     # LangGraph nodes and graph
│   │   ├── rag/          # ChromaDB vector store
│   │   ├── evaluation/   # MLflow tracking
│   │   └── utils/
│   ├── tests/
│   ├── data/
│   │   ├── sample_contracts/
│   │   └── clause_database/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
│   ├── Dockerfile
│   └── package.json
├── .github/workflows/    # CI/CD pipeline
├── docker-compose.yml
└── README.md
```

## License

MIT
