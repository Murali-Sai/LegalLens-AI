from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field

# --- Enums ---

class ClauseType(str, Enum):
    LIABILITY = "liability"
    TERMINATION = "termination"
    IP_OWNERSHIP = "ip_ownership"
    PAYMENT = "payment"
    CONFIDENTIALITY = "confidentiality"
    NON_COMPETE = "non_compete"
    INDEMNIFICATION = "indemnification"
    AUTO_RENEWAL = "auto_renewal"
    OTHER = "other"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# --- Pydantic models for data transfer ---

class DocumentChunk(BaseModel):
    text: str
    chunk_index: int
    page_number: int | None = None
    start_char: int | None = None
    end_char: int | None = None


class ClassifiedClause(BaseModel):
    chunk: DocumentChunk
    clause_type: ClauseType
    confidence: float = Field(ge=0.0, le=1.0)


class BenchmarkResult(BaseModel):
    similar_clauses: list[dict] = []
    similarity_scores: list[float] = []
    is_standard: bool = True
    deviation_summary: str = ""


class FlaggedClause(BaseModel):
    clause: ClassifiedClause
    benchmark: BenchmarkResult
    risk_level: RiskLevel
    risk_reasoning: str


class ExplainedClause(BaseModel):
    flagged: FlaggedClause
    plain_english_summary: str
    recommended_action: str


class AnalysisResult(BaseModel):
    document_id: str
    filename: str
    total_clauses: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    clauses: list[ExplainedClause]


# --- LangGraph state (TypedDict for LangGraph compatibility) ---

class PipelineState(TypedDict, total=False):
    """State that flows through the LangGraph pipeline."""
    document_id: str
    filename: str
    file_bytes: bytes
    raw_text: str
    chunks: list[DocumentChunk]
    classified_clauses: list[ClassifiedClause]
    flagged_clauses: list[FlaggedClause]
    explained_clauses: list[ExplainedClause]
    error: str | None
