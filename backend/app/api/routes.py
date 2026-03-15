import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.core.models import AnalysisResult
from app.pipeline.graph import run_analysis
from app.rag.vector_store import get_collection

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory store for analysis results (swap for DB in production)
_results: dict[str, AnalysisResult] = {}


# --- Request/Response models ---


class HealthResponse(BaseModel):
    status: str
    version: str
    collections: dict[str, int]


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


class StatsResponse(BaseModel):
    total_analyses: int
    total_clauses_processed: int
    high_risk_total: int
    medium_risk_total: int
    low_risk_total: int
    avg_clauses_per_document: float


# --- Endpoints ---


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check with vector store status."""
    try:
        std_count = get_collection("standard_clauses").count()
        risky_count = get_collection("risky_clauses").count()
    except Exception:
        std_count = 0
        risky_count = 0

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        collections={"standard_clauses": std_count, "risky_clauses": risky_count},
    )


@router.post("/upload", response_model=AnalysisResult)
async def upload_document(file: UploadFile):
    """Upload a legal document (PDF/DOCX) for analysis."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("pdf", "docx"):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    contents = await file.read()
    if len(contents) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail=f"File exceeds {settings.max_file_size_mb}MB limit"
        )

    document_id = str(uuid.uuid4())
    logger.info("Starting analysis for %s (id=%s, size=%d bytes)", file.filename, document_id, len(contents))

    start_time = time.time()
    try:
        result = await run_analysis(document_id, file.filename, contents)
    except Exception as e:
        logger.error("Analysis failed for %s: %s", file.filename, str(e))
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    elapsed = time.time() - start_time
    logger.info("Analysis complete in %.1fs — %d clauses found", elapsed, result.total_clauses)

    _results[document_id] = result
    return result


@router.get("/analysis/{document_id}", response_model=AnalysisResult)
async def get_analysis(document_id: str):
    """Retrieve a previously completed analysis by document ID."""
    if document_id not in _results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _results[document_id]


@router.get("/analyses", response_model=list[AnalysisResult])
async def list_analyses():
    """List all completed analyses."""
    return list(_results.values())


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get aggregate statistics across all analyses."""
    if not _results:
        return StatsResponse(
            total_analyses=0,
            total_clauses_processed=0,
            high_risk_total=0,
            medium_risk_total=0,
            low_risk_total=0,
            avg_clauses_per_document=0.0,
        )

    results = list(_results.values())
    total_clauses = sum(r.total_clauses for r in results)

    return StatsResponse(
        total_analyses=len(results),
        total_clauses_processed=total_clauses,
        high_risk_total=sum(r.high_risk_count for r in results),
        medium_risk_total=sum(r.medium_risk_count for r in results),
        low_risk_total=sum(r.low_risk_count for r in results),
        avg_clauses_per_document=total_clauses / len(results) if results else 0.0,
    )


@router.post("/evaluate", response_model=EvaluationResponse)
async def run_evaluation(request: EvaluationRequest):
    """Log evaluation metrics to MLflow."""
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
            detail="No complete metric groups provided. Send precision+recall+f1, mrr_at_5+hit_rate, or risk_accuracy+risk_agreement_rate.",
        )

    return EvaluationResponse(
        status="success",
        metrics_logged=metrics_logged,
        run_ids=run_ids,
    )


@router.post("/evaluate/run")
async def run_automated_evaluation(task: str | None = None):
    """Run automated evaluation against ground truth dataset.

    Args:
        task: Optional filter — "clause", "retrieval", or "risk". Runs all if omitted.
    """
    from app.evaluation.runner import run_all_evaluations

    try:
        results = run_all_evaluations(task=task)
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error("Automated evaluation failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
