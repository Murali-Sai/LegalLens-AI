"""SQLite persistence layer for analysis results."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.models import AnalysisResult

_DB_PATH: Path | None = None


def _db_path() -> Path:
    global _DB_PATH
    if _DB_PATH is None:
        from app.core.config import settings
        base = Path(settings.chroma_persist_dir).parent
        _DB_PATH = base / "legallens.db"
    return _DB_PATH


def _connect() -> sqlite3.Connection:
    """Open a connection, ensuring the directory and schema exist.

    Idempotent — safe to call before the FastAPI lifespan runs (e.g. in tests).
    """
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            document_id TEXT PRIMARY KEY,
            filename    TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            result_json TEXT NOT NULL
        )
    """)
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.commit()


def save_analysis(analysis: AnalysisResult) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO analyses VALUES (?, ?, ?, ?)",
            (
                analysis.document_id,
                analysis.filename,
                datetime.now(timezone.utc).isoformat(),
                analysis.model_dump_json(),
            ),
        )
        conn.commit()


def load_analysis(document_id: str) -> AnalysisResult | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT result_json FROM analyses WHERE document_id = ?",
            (document_id,),
        ).fetchone()
    if not row:
        return None
    return AnalysisResult.model_validate_json(row[0])


def load_all_analyses() -> list[dict]:
    """Return lightweight summaries (no clauses list) ordered newest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT document_id, filename, created_at, result_json FROM analyses "
            "ORDER BY created_at DESC LIMIT 50"
        ).fetchall()

    summaries = []
    for doc_id, filename, created_at, result_json in rows:
        data = json.loads(result_json)
        summaries.append({
            "document_id": doc_id,
            "filename": filename,
            "created_at": created_at,
            "total_clauses": data.get("total_clauses", 0),
            "high_risk_count": data.get("high_risk_count", 0),
            "medium_risk_count": data.get("medium_risk_count", 0),
            "low_risk_count": data.get("low_risk_count", 0),
        })
    return summaries
