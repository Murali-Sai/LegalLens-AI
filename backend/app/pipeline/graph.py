"""LangGraph pipeline: Extract → Analyze → Compare → Flag → Explain"""

import logging

from langgraph.graph import END, StateGraph

from app.core.config import settings
from app.core.models import AnalysisResult, ExplainedClause, PipelineState, RiskLevel
from app.pipeline.nodes import compare_node, extract_node

logger = logging.getLogger(__name__)


def _get_nodes():
    """Return the appropriate node functions based on mock mode."""
    if settings.mock_mode:
        logger.info("MOCK MODE enabled — using keyword-based analysis instead of Claude API")
        from app.pipeline.mock import mock_analyze_node, mock_explain_node, mock_flag_node
        return mock_analyze_node, mock_flag_node, mock_explain_node
    else:
        from app.pipeline.nodes import analyze_node, explain_node, flag_node
        return analyze_node, flag_node, explain_node


def build_graph():
    """Build the 5-step LangGraph reasoning pipeline."""
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


async def run_analysis(document_id: str, filename: str, file_bytes: bytes) -> AnalysisResult:
    """Execute the full analysis pipeline on an uploaded document."""
    logger.info("Starting analysis pipeline for %s (id=%s)", filename, document_id)

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

    explained: list[ExplainedClause] = result_state.get("explained_clauses", [])

    analysis = AnalysisResult(
        document_id=document_id,
        filename=filename,
        total_clauses=len(explained),
        high_risk_count=sum(1 for c in explained if c.flagged.risk_level == RiskLevel.HIGH),
        medium_risk_count=sum(1 for c in explained if c.flagged.risk_level == RiskLevel.MEDIUM),
        low_risk_count=sum(1 for c in explained if c.flagged.risk_level == RiskLevel.LOW),
        clauses=explained,
    )

    logger.info(
        "Analysis complete: %d clauses (%d high, %d medium, %d low risk)",
        analysis.total_clauses,
        analysis.high_risk_count,
        analysis.medium_risk_count,
        analysis.low_risk_count,
    )
    return analysis
