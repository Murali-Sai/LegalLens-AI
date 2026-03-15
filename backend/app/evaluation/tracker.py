"""MLflow evaluation tracking for clause detection, retrieval quality, and risk scoring."""

import logging
from datetime import datetime, timezone

import mlflow

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_mlflow():
    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment("legallens-evaluation")


def log_clause_detection_metrics(
    precision: float, recall: float, f1: float, details: dict | None = None
):
    """Log clause classification metrics with optional per-type breakdown."""
    init_mlflow()
    with mlflow.start_run(run_name=f"clause_detection_{_timestamp()}"):
        mlflow.log_param("model", settings.anthropic_model)
        mlflow.log_param("task", "clause_classification")
        mlflow.log_metrics({
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })
        if details:
            # Log per-clause-type metrics
            for clause_type, metrics in details.items():
                for metric_name, value in metrics.items():
                    mlflow.log_metric(f"{clause_type}_{metric_name}", value)
            # Log details as artifact
            mlflow.log_dict(details, "clause_detection_details.json")


def log_retrieval_metrics(
    mrr_at_5: float, hit_rate: float, details: dict | None = None
):
    """Log RAG retrieval quality metrics."""
    init_mlflow()
    with mlflow.start_run(run_name=f"retrieval_quality_{_timestamp()}"):
        mlflow.log_param("model", "chromadb_default_embedding")
        mlflow.log_param("task", "rag_retrieval")
        mlflow.log_metrics({
            "mrr_at_5": mrr_at_5,
            "hit_rate": hit_rate,
        })
        if details:
            mlflow.log_dict(details, "retrieval_details.json")


def log_risk_scoring_metrics(
    accuracy: float, agreement_rate: float, details: dict | None = None
):
    """Log risk scoring agreement with expert labels."""
    init_mlflow()
    with mlflow.start_run(run_name=f"risk_scoring_{_timestamp()}"):
        mlflow.log_param("model", settings.anthropic_model)
        mlflow.log_param("task", "risk_scoring")
        mlflow.log_metrics({
            "accuracy": accuracy,
            "agreement_rate": agreement_rate,
        })
        if details:
            # Log confusion matrix and per-level breakdown
            mlflow.log_dict(details, "risk_scoring_details.json")


def log_e2e_metrics(
    total_time_seconds: float,
    num_clauses: int,
    num_chunks: int,
    details: dict | None = None,
):
    """Log end-to-end pipeline performance metrics."""
    init_mlflow()
    with mlflow.start_run(run_name=f"e2e_performance_{_timestamp()}"):
        mlflow.log_param("model", settings.anthropic_model)
        mlflow.log_param("task", "e2e_pipeline")
        mlflow.log_metrics({
            "total_time_seconds": total_time_seconds,
            "num_clauses": num_clauses,
            "num_chunks": num_chunks,
            "seconds_per_clause": total_time_seconds / max(num_clauses, 1),
        })
        if details:
            mlflow.log_dict(details, "e2e_details.json")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
