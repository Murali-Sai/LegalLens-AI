import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.config import settings
from app.core.models import AnalysisResult
from app.db import load_all_analyses, load_analysis, save_analysis
from app.pipeline.graph import run_analysis, run_analysis_streaming, run_demo_streaming
from app.rag.vector_store import get_collection

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str
    mock_mode: bool
    collections: dict[str, int]


class StatsResponse(BaseModel):
    total_analyses: int
    total_clauses_processed: int
    high_risk_total: int
    medium_risk_total: int
    low_risk_total: int
    avg_clauses_per_document: float


class EvaluationRequest(BaseModel):
    precision: float | None = None
    recall: float | None = None
    f1: float | None = None
    mrr_at_5: float | None = None
    hit_rate: float | None = None
    risk_accuracy: float | None = None
    risk_agreement_rate: float | None = None


class EvaluationResponse(BaseModel):
    status: str
    metrics_logged: list[str]
    run_ids: dict[str, str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_upload(file: UploadFile, contents: bytes) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    if len(contents) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail=f"File exceeds {settings.max_file_size_mb}MB limit"
        )


def _sse_stream(generator):
    """Wrap an async generator as a StreamingResponse with SSE headers."""
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        std_count = get_collection("standard_clauses").count()
        risky_count = get_collection("risky_clauses").count()
    except Exception:
        std_count = 0
        risky_count = 0

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        mock_mode=settings.effective_mock_mode,
        collections={"standard_clauses": std_count, "risky_clauses": risky_count},
    )


# ---------------------------------------------------------------------------
# Upload — streaming (primary)
# ---------------------------------------------------------------------------

@router.post("/upload-stream")
async def upload_stream(file: UploadFile):
    """Upload a document and receive real-time pipeline progress via SSE.

    Returns a text/event-stream with events:
    - progress: {"step": str, "step_index": int}
    - complete:  <AnalysisResult JSON>
    - error:     <error message>
    """
    contents = await file.read()
    _validate_upload(file, contents)

    document_id = str(uuid.uuid4())
    logger.info(
        "SSE analysis started: %s (id=%s, %d bytes)",
        file.filename, document_id, len(contents),
    )

    return _sse_stream(run_analysis_streaming(document_id, file.filename, contents))


# ---------------------------------------------------------------------------
# Demo — streaming analysis of bundled sample contract
# ---------------------------------------------------------------------------

@router.get("/demo-stream")
async def demo_stream():
    """Stream analysis of the bundled sample contract (no file upload needed)."""
    logger.info("Demo analysis requested")
    return _sse_stream(run_demo_streaming())


# ---------------------------------------------------------------------------
# Upload — legacy synchronous (kept for backwards compatibility / testing)
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=AnalysisResult)
async def upload_document(file: UploadFile):
    contents = await file.read()
    _validate_upload(file, contents)

    document_id = str(uuid.uuid4())
    logger.info("Sync analysis started: %s (id=%s)", file.filename, document_id)

    start = time.time()
    try:
        result = await run_analysis(document_id, file.filename, contents)
    except Exception as e:
        logger.error("Analysis failed for %s: %s", file.filename, str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    logger.info(
        "Analysis complete in %.1fs — %d clauses", time.time() - start, result.total_clauses
    )
    save_analysis(result)
    return result


# ---------------------------------------------------------------------------
# Retrieve analyses
# ---------------------------------------------------------------------------

@router.get("/analysis/{document_id}", response_model=AnalysisResult)
async def get_analysis(document_id: str):
    result = load_analysis(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@router.get("/analyses")
async def list_analyses():
    """Return lightweight summaries of all past analyses (newest first)."""
    return load_all_analyses()


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    summaries = load_all_analyses()
    if not summaries:
        return StatsResponse(
            total_analyses=0,
            total_clauses_processed=0,
            high_risk_total=0,
            medium_risk_total=0,
            low_risk_total=0,
            avg_clauses_per_document=0.0,
        )
    total_clauses = sum(s["total_clauses"] for s in summaries)
    return StatsResponse(
        total_analyses=len(summaries),
        total_clauses_processed=total_clauses,
        high_risk_total=sum(s["high_risk_count"] for s in summaries),
        medium_risk_total=sum(s["medium_risk_count"] for s in summaries),
        low_risk_total=sum(s["low_risk_count"] for s in summaries),
        avg_clauses_per_document=total_clauses / len(summaries),
    )


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=EvaluationResponse)
async def run_evaluation(request: EvaluationRequest):
    from app.evaluation.tracker import (
        log_clause_detection_metrics,
        log_retrieval_metrics,
        log_risk_scoring_metrics,
    )

    metrics_logged = []
    run_ids = {}

    try:
        if request.precision is not None and request.recall is not None and request.f1 is not None:
            log_clause_detection_metrics(request.precision, request.recall, request.f1)
            metrics_logged.extend(["precision", "recall", "f1"])
            run_ids["clause_detection"] = "logged"

        if request.mrr_at_5 is not None and request.hit_rate is not None:
            log_retrieval_metrics(request.mrr_at_5, request.hit_rate)
            metrics_logged.extend(["mrr@5", "hit_rate"])
            run_ids["retrieval_quality"] = "logged"

        if request.risk_accuracy is not None and request.risk_agreement_rate is not None:
            log_risk_scoring_metrics(request.risk_accuracy, request.risk_agreement_rate)
            metrics_logged.extend(["risk_accuracy", "risk_agreement_rate"])
            run_ids["risk_scoring"] = "logged"

    except Exception as e:
        logger.error("Evaluation logging failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"MLflow logging failed: {str(e)}")

    if not metrics_logged:
        raise HTTPException(
            status_code=400,
            detail=(
                "No complete metric groups provided. "
                "Send precision+recall+f1, mrr_at_5+hit_rate, "
                "or risk_accuracy+risk_agreement_rate."
            ),
        )

    return EvaluationResponse(status="success", metrics_logged=metrics_logged, run_ids=run_ids)


@router.post("/evaluate/run")
async def run_automated_evaluation(task: str | None = None):
    from app.evaluation.runner import run_all_evaluations
    try:
        results = run_all_evaluations(task=task)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error("Automated evaluation failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
