"""LangGraph pipeline: Extract → Analyze → Compare → Flag → Explain"""

import asyncio
import json
import logging
from pathlib import Path

from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.core.models import AnalysisResult, ExplainedClause, PipelineState, RiskLevel
from app.pipeline.nodes import compare_node, extract_node

logger = logging.getLogger(__name__)


def _get_nodes():
    """Return node functions — mock when no API key is configured."""
    if settings.effective_mock_mode:
        logger.info("Using keyword-based analysis (mock mode — no API key)")
        from app.pipeline.mock import mock_analyze_node, mock_explain_node, mock_flag_node
        return mock_analyze_node, mock_flag_node, mock_explain_node
    from app.pipeline.nodes import analyze_node, explain_node, flag_node
    return analyze_node, flag_node, explain_node


def build_graph():
    analyze, flag, explain = _get_nodes()
    workflow = StateGraph(PipelineState)
    workflow.add_node("extract", extract_node)
    workflow.add_node("analyze", analyze)
    workflow.add_node("compare", compare_node)
    workflow.add_node("flag", flag)
    workflow.add_node("explain", explain)
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "analyze")
    workflow.add_edge("analyze", "compare")
    workflow.add_edge("compare", "flag")
    workflow.add_edge("flag", "explain")
    workflow.add_edge("explain", END)
    return workflow.compile()


pipeline = build_graph()


def _build_result(document_id: str, filename: str, state: PipelineState) -> AnalysisResult:
    explained: list[ExplainedClause] = state.get("explained_clauses", [])
    return AnalysisResult(
        document_id=document_id,
        filename=filename,
        total_clauses=len(explained),
        high_risk_count=sum(1 for c in explained if c.flagged.risk_level == RiskLevel.HIGH),
        medium_risk_count=sum(1 for c in explained if c.flagged.risk_level == RiskLevel.MEDIUM),
        low_risk_count=sum(1 for c in explained if c.flagged.risk_level == RiskLevel.LOW),
        clauses=explained,
    )


async def run_analysis(document_id: str, filename: str, file_bytes: bytes) -> AnalysisResult:
    """Execute the full pipeline synchronously (used by non-streaming upload)."""
    initial_state: PipelineState = {
        "document_id": document_id,
        "filename": filename,
        "file_bytes": file_bytes,
        "raw_text": "",
        "chunks": [],
        "classified_clauses": [],
        "flagged_clauses": [],
        "explained_clauses": [],
        "error": None,
    }
    result_state = await pipeline.ainvoke(initial_state)
    return _build_result(document_id, filename, result_state)


async def run_analysis_streaming(document_id: str, filename: str, file_bytes: bytes):
    """Run the 5-step pipeline and yield SSE-formatted strings after each step.

    Yields lines like:
        'event: progress\\ndata: {"step": "extract", "step_index": 0}\\n\\n'
        'event: complete\\ndata: {<AnalysisResult JSON>}\\n\\n'
        'event: error\\ndata: <message>\\n\\n'
    """
    analyze, flag, explain = _get_nodes()

    steps = [
        ("extract",  0, extract_node),
        ("analyze",  1, analyze),
        ("compare",  2, compare_node),
        ("flag",     3, flag),
        ("explain",  4, explain),
    ]

    state: PipelineState = {
        "document_id": document_id,
        "filename": filename,
        "file_bytes": file_bytes,
        "raw_text": "",
        "chunks": [],
        "classified_clauses": [],
        "flagged_clauses": [],
        "explained_clauses": [],
        "error": None,
    }

    loop = asyncio.get_event_loop()
    try:
        for step_name, step_idx, node_fn in steps:
            logger.info("Streaming step %d/5: %s", step_idx + 1, step_name)
            updates = await loop.run_in_executor(None, node_fn, state)
            state.update(updates)
            payload = json.dumps({"step": step_name, "step_index": step_idx})
            yield f"event: progress\ndata: {payload}\n\n"

        analysis = _build_result(document_id, filename, state)

        from app.db import save_analysis
        save_analysis(analysis)

        yield f"event: complete\ndata: {analysis.model_dump_json()}\n\n"

    except Exception as exc:
        logger.error("Streaming analysis failed: %s", exc, exc_info=True)
        yield f"event: error\ndata: {json.dumps(str(exc))}\n\n"


async def run_demo_streaming():
    """Stream analysis of the bundled sample contract."""
    import uuid
    sample = Path(__file__).resolve().parent.parent.parent / "data/sample_contracts/test_agreement.docx"
    if not sample.exists():
        yield f"event: error\ndata: {json.dumps('Sample contract not found')}\n\n"
        return
    document_id = "demo-" + str(uuid.uuid4())[:8]
    async for chunk in run_analysis_streaming(document_id, "sample_contract.docx", sample.read_bytes()):
        yield chunk
