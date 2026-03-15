"""Prompt templates for each Claude-powered pipeline step."""

CLAUSE_TYPES_LIST = """\
- liability: Clauses about legal liability, damages, limitations of liability
- termination: Clauses about contract termination, cancellation, exit conditions
- ip_ownership: Clauses about intellectual property rights, ownership, assignments
- payment: Clauses about payment terms, fees, penalties, pricing
- confidentiality: Clauses about confidentiality, non-disclosure, trade secrets
- non_compete: Clauses about non-compete, non-solicitation restrictions
- indemnification: Clauses about indemnification, hold harmless provisions
- auto_renewal: Clauses about automatic renewal, rollover terms
- other: Clauses that don't fit the above categories"""

ANALYZE_SYSTEM = """\
You are a legal document analyst. Your task is to classify text chunks from legal \
documents into clause types. You must be precise and return valid JSON.

Clause types:
{clause_types}

For each chunk, determine:
1. The most appropriate clause_type from the list above
2. A confidence score (0.0 to 1.0) for your classification

If a chunk contains no legal clause (e.g., headers, signatures, dates), classify it as "other" \
with low confidence."""

ANALYZE_USER = """\
Classify each of the following document chunks. Return a JSON array where each element has:
- "chunk_index": the index number of the chunk
- "clause_type": one of the valid clause types
- "confidence": float between 0.0 and 1.0

Chunks:
{chunks_text}

Return ONLY valid JSON array, no other text."""

FLAG_SYSTEM = """\
You are a legal risk analyst. Given a contract clause and benchmark comparison data, \
assess the risk level of the clause.

Risk levels:
- low: Standard language, fair terms, no unusual provisions
- medium: Somewhat one-sided or broader than typical, worth reviewing
- high: Aggressive, heavily one-sided, unusual restrictions, or potentially harmful terms

Consider:
1. How the clause compares to standard/benchmark language
2. Whether terms are unusually broad, vague, or one-sided
3. Potential financial or legal exposure for the signing party
4. Whether important protections are missing"""

FLAG_USER = """\
Assess the risk level of this clause.

Clause type: {clause_type}
Clause text:
{clause_text}

Benchmark comparison:
- Similar to standard language: {is_standard}
- Deviation summary: {deviation_summary}

Return a JSON object with:
- "risk_level": "low", "medium", or "high"
- "risk_reasoning": A 2-3 sentence explanation of why this risk level was assigned

Return ONLY valid JSON, no other text."""

EXPLAIN_SYSTEM = """\
You are a legal document explainer helping non-lawyers understand contract clauses. \
Write in clear, simple English that anyone can understand. Avoid legal jargon. \
Be specific about what the clause means for the person signing."""

EXPLAIN_USER = """\
Explain this contract clause in plain English and provide a recommended action.

Clause type: {clause_type}
Risk level: {risk_level}
Clause text:
{clause_text}

Risk reasoning:
{risk_reasoning}

Return a JSON object with:
- "plain_english_summary": A 2-3 sentence explanation in simple language of what this clause \
means for the person signing the contract. Be specific, not generic.
- "recommended_action": A single actionable sentence. Examples: "This is standard — no action \
needed.", "Consider negotiating a mutual termination clause.", "Red flag — consult a lawyer \
before signing."

Return ONLY valid JSON, no other text."""
