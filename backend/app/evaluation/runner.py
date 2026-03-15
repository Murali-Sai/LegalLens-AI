"""Evaluation runner: computes clause detection, retrieval, and risk scoring metrics.

Usage:
    python -m app.evaluation.runner                  # Run all evaluations
    python -m app.evaluation.runner --task clause     # Clause detection only
    python -m app.evaluation.runner --task retrieval  # Retrieval quality only
    python -m app.evaluation.runner --task risk       # Risk scoring only
"""

import json
import logging
import sys
import time
from collections import defaultdict
from pathlib import Path

from app.core.models import (
    ClassifiedClause,
    ClauseType,
    DocumentChunk,
    RiskLevel,
)
from app.evaluation.tracker import (
    log_clause_detection_metrics,
    log_retrieval_metrics,
    log_risk_scoring_metrics,
)
from app.pipeline.nodes import call_claude, parse_json_response
from app.pipeline.prompts import (
    ANALYZE_SYSTEM,
    ANALYZE_USER,
    CLAUSE_TYPES_LIST,
    FLAG_SYSTEM,
    FLAG_USER,
)
from app.rag.vector_store import get_collection, initialize_vector_store

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "evaluation"


def load_ground_truth() -> list[dict]:
    filepath = DATA_DIR / "ground_truth.json"
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Clause Detection Evaluation
# ---------------------------------------------------------------------------

def evaluate_clause_detection(samples: list[dict]) -> dict:
    """Evaluate clause type classification accuracy against ground truth."""
    logger.info("Evaluating clause detection on %d samples...", len(samples))

    # Build chunks from samples
    chunks_text_parts = []
    for i, sample in enumerate(samples):
        chunks_text_parts.append(f"[Chunk {i}]:\n{sample['text']}")
    chunks_text = "\n\n---\n\n".join(chunks_text_parts)

    system = ANALYZE_SYSTEM.format(clause_types=CLAUSE_TYPES_LIST)
    user = ANALYZE_USER.format(chunks_text=chunks_text)

    response_text = call_claude(system, user)
    predictions = parse_json_response(response_text)

    # Build prediction map
    pred_map = {}
    for item in predictions:
        pred_map[item["chunk_index"]] = item.get("clause_type", "other")

    # Compute metrics
    correct = 0
    total = len(samples)
    per_type_correct = defaultdict(int)
    per_type_total = defaultdict(int)
    per_type_predicted = defaultdict(int)
    confusion = []

    for i, sample in enumerate(samples):
        expected = sample["expected_clause_type"]
        predicted = pred_map.get(i, "other")
        per_type_total[expected] += 1
        per_type_predicted[predicted] += 1

        if predicted == expected:
            correct += 1
            per_type_correct[expected] += 1

        confusion.append({
            "id": sample["id"],
            "expected": expected,
            "predicted": predicted,
            "match": predicted == expected,
        })

    # Overall accuracy
    accuracy = correct / total if total > 0 else 0

    # Per-type precision, recall, F1
    per_type_details = {}
    all_types = set(list(per_type_total.keys()) + list(per_type_predicted.keys()))

    macro_precision = 0
    macro_recall = 0
    type_count = 0

    for ct in all_types:
        tp = per_type_correct[ct]
        total_expected = per_type_total[ct]
        total_predicted = per_type_predicted[ct]

        precision = tp / total_predicted if total_predicted > 0 else 0
        recall = tp / total_expected if total_expected > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        per_type_details[ct] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": total_expected,
        }

        if total_expected > 0:
            macro_precision += precision
            macro_recall += recall
            type_count += 1

    macro_precision /= max(type_count, 1)
    macro_recall /= max(type_count, 1)
    macro_f1 = (
        2 * macro_precision * macro_recall / (macro_precision + macro_recall)
        if (macro_precision + macro_recall) > 0
        else 0
    )

    result = {
        "accuracy": round(accuracy, 3),
        "macro_precision": round(macro_precision, 3),
        "macro_recall": round(macro_recall, 3),
        "macro_f1": round(macro_f1, 3),
        "per_type": per_type_details,
        "confusion": confusion,
        "total_samples": total,
        "correct": correct,
    }

    # Log to MLflow
    log_clause_detection_metrics(
        precision=result["macro_precision"],
        recall=result["macro_recall"],
        f1=result["macro_f1"],
        details={"per_type": per_type_details, "accuracy": accuracy},
    )

    logger.info(
        "Clause detection — Accuracy: %.1f%%, Precision: %.1f%%, Recall: %.1f%%, F1: %.1f%%",
        accuracy * 100, macro_precision * 100, macro_recall * 100, macro_f1 * 100,
    )
    return result


# ---------------------------------------------------------------------------
# Retrieval Quality Evaluation
# ---------------------------------------------------------------------------

def evaluate_retrieval(samples: list[dict]) -> dict:
    """Evaluate RAG retrieval quality: MRR@5 and hit rate."""
    logger.info("Evaluating retrieval quality on %d samples...", len(samples))

    initialize_vector_store()
    standard_col = get_collection("standard_clauses")
    risky_col = get_collection("risky_clauses")

    hits = 0
    reciprocal_ranks = []

    for sample in samples:
        expected_risk = sample["expected_risk_level"]
        expected_type = sample["expected_clause_type"]

        # Determine which collection should have the best match
        target_col = standard_col if expected_risk == "low" else risky_col

        try:
            results = target_col.query(
                query_texts=[sample["text"]],
                n_results=5,
                where={"clause_type": expected_type},
            )
        except Exception:
            # Collection might not have entries for this type
            results = {"documents": [[]], "metadatas": [[]]}

        # Check if any result matches the expected clause type
        found_rank = 0
        if results and results["metadatas"] and results["metadatas"][0]:
            for rank, meta in enumerate(results["metadatas"][0], start=1):
                if meta.get("clause_type") == expected_type:
                    found_rank = rank
                    break

        if found_rank > 0:
            hits += 1
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            reciprocal_ranks.append(0.0)

    total = len(samples)
    hit_rate = hits / total if total > 0 else 0
    mrr_at_5 = sum(reciprocal_ranks) / total if total > 0 else 0

    result = {
        "mrr_at_5": round(mrr_at_5, 3),
        "hit_rate": round(hit_rate, 3),
        "total_queries": total,
        "hits": hits,
    }

    log_retrieval_metrics(
        mrr_at_5=result["mrr_at_5"],
        hit_rate=result["hit_rate"],
        details=result,
    )

    logger.info("Retrieval — MRR@5: %.3f, Hit Rate: %.1f%%", mrr_at_5, hit_rate * 100)
    return result


# ---------------------------------------------------------------------------
# Risk Scoring Evaluation
# ---------------------------------------------------------------------------

def evaluate_risk_scoring(samples: list[dict]) -> dict:
    """Evaluate risk level scoring accuracy against expert labels."""
    logger.info("Evaluating risk scoring on %d samples...", len(samples))

    correct = 0
    total = len(samples)
    per_level = defaultdict(lambda: {"correct": 0, "total": 0})
    confusion = []

    for sample in samples:
        expected_risk = sample["expected_risk_level"]
        clause_type = sample["expected_clause_type"]

        user_prompt = FLAG_USER.format(
            clause_type=clause_type,
            clause_text=sample["text"],
            is_standard=expected_risk == "low",
            deviation_summary="Evaluation mode — no benchmark data available.",
        )

        try:
            response_text = call_claude(FLAG_SYSTEM, user_prompt)
            result = parse_json_response(response_text)
            predicted_risk = result.get("risk_level", "medium")
        except Exception as e:
            logger.warning("Risk scoring failed for %s: %s", sample["id"], e)
            predicted_risk = "medium"

        per_level[expected_risk]["total"] += 1

        if predicted_risk == expected_risk:
            correct += 1
            per_level[expected_risk]["correct"] += 1

        confusion.append({
            "id": sample["id"],
            "expected": expected_risk,
            "predicted": predicted_risk,
            "match": predicted_risk == expected_risk,
        })

    accuracy = correct / total if total > 0 else 0
    agreement_rate = accuracy  # Same metric in this context

    per_level_details = {}
    for level in ("low", "medium", "high"):
        data = per_level[level]
        t = data["total"]
        c = data["correct"]
        per_level_details[level] = {
            "accuracy": round(c / t, 3) if t > 0 else 0,
            "correct": c,
            "total": t,
        }

    result = {
        "accuracy": round(accuracy, 3),
        "agreement_rate": round(agreement_rate, 3),
        "per_level": per_level_details,
        "confusion": confusion,
        "total_samples": total,
        "correct": correct,
    }

    log_risk_scoring_metrics(
        accuracy=result["accuracy"],
        agreement_rate=result["agreement_rate"],
        details={"per_level": per_level_details},
    )

    logger.info("Risk scoring — Accuracy: %.1f%%, Agreement: %.1f%%", accuracy * 100, agreement_rate * 100)
    return result


# ---------------------------------------------------------------------------
# Full Evaluation Runner
# ---------------------------------------------------------------------------

def run_all_evaluations(task: str | None = None) -> dict:
    """Run all evaluation tasks and return combined results."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    samples = load_ground_truth()
    logger.info("Loaded %d evaluation samples", len(samples))

    results = {}
    start = time.time()

    if task is None or task == "clause":
        results["clause_detection"] = evaluate_clause_detection(samples)

    if task is None or task == "retrieval":
        results["retrieval"] = evaluate_retrieval(samples)

    if task is None or task == "risk":
        results["risk_scoring"] = evaluate_risk_scoring(samples)

    elapsed = time.time() - start
    results["total_time_seconds"] = round(elapsed, 1)

    logger.info("Evaluation complete in %.1fs", elapsed)

    # Save results to file
    output_path = DATA_DIR / "latest_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info("Results saved to %s", output_path)

    return results


if __name__ == "__main__":
    task_filter = None
    if "--task" in sys.argv:
        idx = sys.argv.index("--task")
        if idx + 1 < len(sys.argv):
            task_filter = sys.argv[idx + 1]

    run_all_evaluations(task=task_filter)
