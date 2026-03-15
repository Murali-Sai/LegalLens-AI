"""Pipeline node implementations — one function per reasoning step."""

import json
import logging
import tempfile
from pathlib import Path

import anthropic

from app.core.config import settings
from app.core.models import (
    BenchmarkResult,
    ClassifiedClause,
    ClauseType,
    DocumentChunk,
    ExplainedClause,
    FlaggedClause,
    PipelineState,
    RiskLevel,
)
from app.pipeline.prompts import (
    ANALYZE_SYSTEM,
    ANALYZE_USER,
    CLAUSE_TYPES_LIST,
    EXPLAIN_SYSTEM,
    EXPLAIN_USER,
    FLAG_SYSTEM,
    FLAG_USER,
)
from app.rag.vector_store import get_collection

logger = logging.getLogger(__name__)

# Shared Claude client (lazy init)
_client: anthropic.Anthropic | None = None


def get_claude_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def call_claude(system: str, user: str) -> str:
    """Make a synchronous Claude API call and return the text response."""
    client = get_claude_client()
    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return message.content[0].text


def parse_json_response(text: str) -> dict | list:
    """Extract JSON from Claude's response, handling markdown code blocks."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()
    return json.loads(cleaned)


# ---------------------------------------------------------------------------
# Step 1: EXTRACT — Parse uploaded document into text chunks
# ---------------------------------------------------------------------------

def extract_node(state: PipelineState) -> dict:
    """Parse PDF/DOCX into text chunks using Unstructured.io."""
    logger.info("Step 1/5: Extracting text from %s", state.get("filename", "document"))

    file_bytes = state["file_bytes"]
    filename = state.get("filename", "document.pdf")
    suffix = Path(filename).suffix.lower()

    # Write bytes to temp file for Unstructured
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if suffix == ".docx":
            from unstructured.partition.docx import partition_docx
            elements = partition_docx(filename=tmp_path)
        elif suffix == ".pdf":
            try:
                from unstructured.partition.pdf import partition_pdf
                elements = partition_pdf(filename=tmp_path, strategy="fast")
            except (ImportError, ModuleNotFoundError):
                # Fallback: use PyMuPDF which handles most PDFs well
                logger.warning(
                    "unstructured_inference not available, using PyMuPDF fallback for PDF"
                )
                import fitz  # PyMuPDF
                from unstructured.partition.text import partition_text
                doc = fitz.open(tmp_path)
                pages = []
                for page in doc:
                    pages.append(page.get_text())
                doc.close()
                raw = "\n".join(pages)
                if not raw.strip():
                    logger.warning("PyMuPDF extracted no text — PDF may be image-only/scanned")
                elements = partition_text(text=raw) if raw.strip() else []
        else:
            from unstructured.partition.auto import partition
            elements = partition(filename=tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # Build chunks from elements
    raw_parts: list[str] = []
    chunks: list[DocumentChunk] = []
    current_chunk_text = ""
    chunk_index = 0
    char_offset = 0

    for element in elements:
        text = str(element).strip()
        if not text:
            continue

        raw_parts.append(text)

        # Accumulate text into chunks of roughly 500-1000 chars
        current_chunk_text += (" " if current_chunk_text else "") + text

        if len(current_chunk_text) >= 500:
            page_num = None
            if hasattr(element, "metadata") and hasattr(element.metadata, "page_number"):
                page_num = element.metadata.page_number

            chunks.append(DocumentChunk(
                text=current_chunk_text.strip(),
                chunk_index=chunk_index,
                page_number=page_num,
                start_char=char_offset,
                end_char=char_offset + len(current_chunk_text),
            ))
            char_offset += len(current_chunk_text)
            chunk_index += 1
            current_chunk_text = ""

    # Flush remaining text as final chunk
    if current_chunk_text.strip():
        chunks.append(DocumentChunk(
            text=current_chunk_text.strip(),
            chunk_index=chunk_index,
            page_number=None,
            start_char=char_offset,
            end_char=char_offset + len(current_chunk_text),
        ))

    raw_text = "\n\n".join(raw_parts)
    logger.info("Extracted %d chunks from document", len(chunks))

    return {"raw_text": raw_text, "chunks": chunks}


# ---------------------------------------------------------------------------
# Step 2: ANALYZE — Classify each chunk by clause type using Claude
# ---------------------------------------------------------------------------

def analyze_node(state: PipelineState) -> dict:
    """Classify each chunk by clause type using Claude."""
    chunks = state["chunks"]
    logger.info("Step 2/5: Analyzing %d chunks for clause types", len(chunks))

    if not chunks:
        return {"classified_clauses": []}

    # Build chunks text for the prompt (batch all chunks in one call for efficiency)
    chunks_text_parts = []
    for chunk in chunks:
        chunks_text_parts.append(f"[Chunk {chunk.chunk_index}]:\n{chunk.text}")
    chunks_text = "\n\n---\n\n".join(chunks_text_parts)

    system = ANALYZE_SYSTEM.format(clause_types=CLAUSE_TYPES_LIST)
    user = ANALYZE_USER.format(chunks_text=chunks_text)

    response_text = call_claude(system, user)
    classifications = parse_json_response(response_text)

    # Build ClassifiedClause objects
    chunk_map = {c.chunk_index: c for c in chunks}
    classified: list[ClassifiedClause] = []

    for item in classifications:
        idx = item["chunk_index"]
        if idx not in chunk_map:
            continue

        clause_type_str = item.get("clause_type", "other")
        try:
            clause_type = ClauseType(clause_type_str)
        except ValueError:
            clause_type = ClauseType.OTHER

        confidence = max(0.0, min(1.0, float(item.get("confidence", 0.5))))

        classified.append(ClassifiedClause(
            chunk=chunk_map[idx],
            clause_type=clause_type,
            confidence=confidence,
        ))

    # Filter out low-confidence "other" clauses (likely headers/footers)
    classified = [
        c for c in classified
        if not (c.clause_type == ClauseType.OTHER and c.confidence < 0.4)
    ]

    logger.info("Classified %d clauses (filtered from %d chunks)", len(classified), len(chunks))
    return {"classified_clauses": classified}


# ---------------------------------------------------------------------------
# Step 3: COMPARE — Retrieve similar clauses from ChromaDB for benchmarking
# ---------------------------------------------------------------------------

def compare_node(state: PipelineState) -> dict:
    """Retrieve similar clauses from vector store to benchmark each clause."""
    classified = state.get("classified_clauses", [])
    logger.info("Step 3/5: Comparing %d clauses against benchmark database", len(classified))

    flagged: list[FlaggedClause] = []

    for clause in classified:
        benchmark = _benchmark_clause(clause)

        # Store as FlaggedClause with placeholder risk — flag_node will override
        flagged.append(FlaggedClause(
            clause=clause,
            benchmark=benchmark,
            risk_level=RiskLevel.LOW,
            risk_reasoning="",
        ))

    return {"flagged_clauses": flagged}


def _benchmark_clause(clause: ClassifiedClause) -> BenchmarkResult:
    """Query ChromaDB for similar standard and risky clauses."""
    try:
        standard_col = get_collection("standard_clauses")
        risky_col = get_collection("risky_clauses")

        clause_text = clause.chunk.text

        # Query standard clauses
        std_results = standard_col.query(
            query_texts=[clause_text],
            n_results=3,
            where={"clause_type": clause.clause_type.value},
        )

        # Query risky clauses
        risky_results = risky_col.query(
            query_texts=[clause_text],
            n_results=3,
            where={"clause_type": clause.clause_type.value},
        )

        similar_clauses = []
        similarity_scores = []

        # Process standard results
        if std_results and std_results["documents"] and std_results["documents"][0]:
            for i, doc in enumerate(std_results["documents"][0]):
                distance = std_results["distances"][0][i] if std_results.get("distances") else 1.0
                similarity = max(0.0, 1.0 - distance)
                similar_clauses.append({
                    "text": doc,
                    "source": "standard",
                    "similarity": similarity,
                })
                similarity_scores.append(similarity)

        # Process risky results
        if risky_results and risky_results["documents"] and risky_results["documents"][0]:
            for i, doc in enumerate(risky_results["documents"][0]):
                dist = risky_results["distances"][0][i]
                distance = dist if risky_results.get("distances") else 1.0
                similarity = max(0.0, 1.0 - distance)
                similar_clauses.append({
                    "text": doc,
                    "source": "risky",
                    "similarity": similarity,
                })
                similarity_scores.append(similarity)

        # Determine if clause is standard
        std_max = max(
            (c["similarity"] for c in similar_clauses if c["source"] == "standard"),
            default=0,
        )
        risky_max = max(
            (c["similarity"] for c in similar_clauses if c["source"] == "risky"),
            default=0,
        )
        is_standard = std_max >= risky_max and std_max > 0.3

        deviation = ""
        if not is_standard and risky_max > 0.3:
            deviation = (
                "This clause is more similar to known risky clause patterns than standard ones."
            )
        elif std_max < 0.3 and risky_max < 0.3:
            deviation = "No close matches found in the benchmark database — clause may be unusual."

        return BenchmarkResult(
            similar_clauses=similar_clauses,
            similarity_scores=similarity_scores,
            is_standard=is_standard,
            deviation_summary=deviation,
        )

    except Exception as e:
        logger.warning("Benchmark query failed (DB may be empty): %s", e)
        return BenchmarkResult(
            similar_clauses=[],
            similarity_scores=[],
            is_standard=True,
            deviation_summary="Benchmark database not yet populated — using LLM judgment only.",
        )


# ---------------------------------------------------------------------------
# Step 4: FLAG — Score each clause by risk level with reasoning
# ---------------------------------------------------------------------------

def flag_node(state: PipelineState) -> dict:
    """Score each clause by risk level using Claude."""
    flagged = state.get("flagged_clauses", [])
    logger.info("Step 4/5: Scoring risk for %d clauses", len(flagged))

    updated: list[FlaggedClause] = []

    for item in flagged:
        user_prompt = FLAG_USER.format(
            clause_type=item.clause.clause_type.value,
            clause_text=item.clause.chunk.text,
            is_standard=item.benchmark.is_standard,
            deviation_summary=(
                item.benchmark.deviation_summary or "No significant deviations found."
            ),
        )

        response_text = call_claude(FLAG_SYSTEM, user_prompt)
        result = parse_json_response(response_text)

        try:
            risk_level = RiskLevel(result["risk_level"])
        except (ValueError, KeyError):
            risk_level = RiskLevel.MEDIUM

        risk_reasoning = result.get("risk_reasoning", "Unable to determine risk reasoning.")

        updated.append(FlaggedClause(
            clause=item.clause,
            benchmark=item.benchmark,
            risk_level=risk_level,
            risk_reasoning=risk_reasoning,
        ))

    logger.info(
        "Risk breakdown: %d high, %d medium, %d low",
        sum(1 for c in updated if c.risk_level == RiskLevel.HIGH),
        sum(1 for c in updated if c.risk_level == RiskLevel.MEDIUM),
        sum(1 for c in updated if c.risk_level == RiskLevel.LOW),
    )
    return {"flagged_clauses": updated}


# ---------------------------------------------------------------------------
# Step 5: EXPLAIN — Generate plain-English summaries and recommended actions
# ---------------------------------------------------------------------------

def explain_node(state: PipelineState) -> dict:
    """Generate plain-English explanations and recommended actions using Claude."""
    flagged = state.get("flagged_clauses", [])
    logger.info("Step 5/5: Generating explanations for %d clauses", len(flagged))

    explained: list[ExplainedClause] = []

    for item in flagged:
        user_prompt = EXPLAIN_USER.format(
            clause_type=item.clause.clause_type.value,
            risk_level=item.risk_level.value,
            clause_text=item.clause.chunk.text,
            risk_reasoning=item.risk_reasoning,
        )

        response_text = call_claude(EXPLAIN_SYSTEM, user_prompt)
        result = parse_json_response(response_text)

        explained.append(ExplainedClause(
            flagged=item,
            plain_english_summary=result.get("plain_english_summary", "Summary unavailable."),
            recommended_action=result.get("recommended_action", "Review this clause carefully."),
        ))

    logger.info("Generated explanations for %d clauses", len(explained))
    return {"explained_clauses": explained}
