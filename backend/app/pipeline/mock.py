"""Mock implementations for testing without Claude API credits."""

import logging

from app.core.models import (
    ClassifiedClause,
    ClauseType,
    DocumentChunk,
    ExplainedClause,
    FlaggedClause,
    PipelineState,
    RiskLevel,
)

logger = logging.getLogger(__name__)

# Keyword-based clause classification rules
_CLAUSE_KEYWORDS: dict[ClauseType, list[str]] = {
    ClauseType.LIABILITY: [
        "liab", "damages", "limitation of liability",
        "not liable", "waive",
    ],
    ClauseType.TERMINATION: [
        "terminat", "cancel", "expir",
        "end of term", "early departure",
    ],
    ClauseType.IP_OWNERSHIP: [
        "intellectual property", "ip ", "patent", "copyright",
        "invention", "work made for hire", "assigns to",
    ],
    ClauseType.PAYMENT: [
        "payment", "invoice", "fee", "rent",
        "compensat", "late fee", "refund",
    ],
    ClauseType.CONFIDENTIALITY: [
        "confidential", "non-disclosure", "nda",
        "trade secret", "proprietary",
    ],
    ClauseType.NON_COMPETE: [
        "non-compete", "non compete", "noncompete",
        "not engage", "competitive", "not work for",
    ],
    ClauseType.INDEMNIFICATION: [
        "indemnif", "hold harmless", "defend and hold",
    ],
    ClauseType.AUTO_RENEWAL: [
        "auto-renew", "automatic renewal", "renew",
        "auto renewal", "successive",
    ],
}

# Risk indicators
_HIGH_RISK_KEYWORDS = [
    "under no circumstances", "any damages whatsoever",
    "waives all rights", "sole discretion", "without notice",
    "no refund", "in perpetuity", "anywhere in the world",
    "whether or not related", "own time",
    "five (5) years", "three (3) year", "180 days", "25%",
    "even if", "regardless of cause", "including direct damages",
    "provider's own negligence", "repay all compensation",
]

_LOW_RISK_KEYWORDS = [
    "either party", "mutual", "reasonable",
    "thirty (30) days", "cure period", "written notice",
    "twelve (12) months", "publicly available",
    "independently developed",
    "1.5%", "five percent", "50-mile", "direct competitors",
]

# Mock explanations by clause type and risk
_MOCK_EXPLANATIONS = {
    (ClauseType.LIABILITY, RiskLevel.HIGH): {
        "summary": (
            "This clause completely eliminates the provider's "
            "responsibility for any harm they cause you. Even if "
            "their service fails entirely and costs you money, "
            "you cannot hold them accountable for any damages."
        ),
        "action": (
            "Red flag \u2014 this removes all your legal protections. "
            "Negotiate for at least a mutual liability cap "
            "tied to fees paid."
        ),
    },
    (ClauseType.LIABILITY, RiskLevel.LOW): {
        "summary": (
            "Both parties agree to limit their liability for "
            "indirect damages like lost profits. This is a "
            "standard protection that keeps the contract fair "
            "for both sides."
        ),
        "action": "This is standard \u2014 no action needed.",
    },
    (ClauseType.TERMINATION, RiskLevel.HIGH): {
        "summary": (
            "The provider can leave at any time without warning, "
            "but you're locked in with a 90-day notice period and "
            "an early exit fee equal to the full remaining contract "
            "value. This is heavily one-sided."
        ),
        "action": (
            "Red flag \u2014 negotiate for mutual termination rights "
            "with equal notice periods."
        ),
    },
    (ClauseType.TERMINATION, RiskLevel.LOW): {
        "summary": (
            "Either side can end the agreement with 30 days "
            "written notice. This gives both parties a fair "
            "and equal exit path."
        ),
        "action": "This is standard \u2014 no action needed.",
    },
    (ClauseType.IP_OWNERSHIP, RiskLevel.HIGH): {
        "summary": (
            "This clause claims ownership over everything you "
            "create during employment, even personal projects "
            "built on your own time with your own tools that "
            "have nothing to do with the company's business."
        ),
        "action": (
            "Red flag \u2014 negotiate to limit IP assignment to work "
            "related to company business only. Many states "
            "(like California) make this unenforceable."
        ),
    },
    (ClauseType.IP_OWNERSHIP, RiskLevel.LOW): {
        "summary": (
            "Work you create as part of this engagement belongs "
            "to the client. This is standard for contractor "
            "and employment agreements."
        ),
        "action": "This is standard \u2014 no action needed.",
    },
    (ClauseType.PAYMENT, RiskLevel.HIGH): {
        "summary": (
            "You must pay everything upfront with absolutely no "
            "refunds, even if the provider fails to deliver. "
            "Late fees are excessive with no grace period."
        ),
        "action": (
            "Red flag \u2014 negotiate for milestone-based payments "
            "and a reasonable refund policy for undelivered "
            "services."
        ),
    },
    (ClauseType.PAYMENT, RiskLevel.LOW): {
        "summary": (
            "You have 30 days to pay invoices, with a reasonable "
            "1.5% monthly late fee. This is standard commercial "
            "payment terms."
        ),
        "action": "This is standard \u2014 no action needed.",
    },
    (ClauseType.CONFIDENTIALITY, RiskLevel.HIGH): {
        "summary": (
            "You must keep everything confidential forever, with "
            "no exceptions even for court orders. This could put "
            "you in legal jeopardy if compelled to disclose."
        ),
        "action": (
            "Red flag \u2014 insist on standard exclusions for publicly "
            "available info, court orders, and a reasonable time "
            "limit (2-3 years)."
        ),
    },
    (ClauseType.CONFIDENTIALITY, RiskLevel.LOW): {
        "summary": (
            "Both parties agree to protect each other's "
            "confidential information for 2 years, with standard "
            "exceptions for public information."
        ),
        "action": "This is standard \u2014 no action needed.",
    },
    (ClauseType.NON_COMPETE, RiskLevel.HIGH): {
        "summary": (
            "You cannot work in any similar business anywhere in "
            "the world for 5 years after leaving. This could "
            "prevent you from working in your entire field."
        ),
        "action": (
            "Red flag \u2014 this is almost certainly unenforceable. "
            "Negotiate to narrow the scope, geography "
            "(50-mile radius), and duration (6-12 months)."
        ),
    },
    (ClauseType.NON_COMPETE, RiskLevel.LOW): {
        "summary": (
            "For 12 months after leaving, you cannot work for "
            "direct competitors within 50 miles. This is a "
            "reasonably scoped restriction."
        ),
        "action": "This is standard \u2014 no action needed.",
    },
    (ClauseType.INDEMNIFICATION, RiskLevel.HIGH): {
        "summary": (
            "You must cover the provider's legal costs even when "
            "the problem was caused by the provider's own "
            "mistakes or negligence."
        ),
        "action": (
            "Red flag \u2014 negotiate for mutual indemnification "
            "that only covers each party's own breaches."
        ),
    },
    (ClauseType.INDEMNIFICATION, RiskLevel.LOW): {
        "summary": (
            "Each party agrees to cover the other's costs if "
            "they cause a problem through their own breach or "
            "negligence. This is fair and mutual."
        ),
        "action": "This is standard \u2014 no action needed.",
    },
    (ClauseType.AUTO_RENEWAL, RiskLevel.HIGH): {
        "summary": (
            "The contract auto-renews for 3 years with only a "
            "narrow 180-day cancellation window. Missing this "
            "window locks you in for another full term."
        ),
        "action": (
            "Red flag \u2014 negotiate for annual renewal with "
            "30-60 day cancellation notice."
        ),
    },
    (ClauseType.AUTO_RENEWAL, RiskLevel.LOW): {
        "summary": (
            "The agreement auto-renews annually unless you give "
            "60 days notice. This is a standard renewal clause "
            "with a reasonable opt-out window."
        ),
        "action": "This is standard \u2014 no action needed.",
    },
}


def _classify_chunk(chunk: DocumentChunk) -> tuple[ClauseType, float]:
    """Classify a chunk using keyword matching."""
    text_lower = chunk.text.lower()
    best_type = ClauseType.OTHER
    best_score = 0.0

    for clause_type, keywords in _CLAUSE_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > best_score:
            best_score = matches
            best_type = clause_type

    confidence = (
        min(0.95, 0.5 + best_score * 0.15) if best_score > 0 else 0.2
    )
    return best_type, confidence


def _score_risk(text: str) -> RiskLevel:
    """Score risk using keyword heuristics."""
    text_lower = text.lower()
    high_hits = sum(
        1 for kw in _HIGH_RISK_KEYWORDS if kw in text_lower
    )
    low_hits = sum(
        1 for kw in _LOW_RISK_KEYWORDS if kw in text_lower
    )

    if high_hits >= 2:
        return RiskLevel.HIGH
    elif high_hits >= 1 and low_hits == 0:
        return RiskLevel.HIGH
    elif low_hits >= 2:
        return RiskLevel.LOW
    elif high_hits > 0:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


def mock_analyze_node(state: PipelineState) -> dict:
    """Mock clause classification using keyword matching."""
    chunks = state["chunks"]
    logger.info(
        "[MOCK] Step 2/5: Analyzing %d chunks", len(chunks),
    )

    classified: list[ClassifiedClause] = []
    for chunk in chunks:
        clause_type, confidence = _classify_chunk(chunk)
        if clause_type == ClauseType.OTHER and confidence < 0.4:
            continue
        classified.append(ClassifiedClause(
            chunk=chunk,
            clause_type=clause_type,
            confidence=confidence,
        ))

    logger.info("[MOCK] Classified %d clauses", len(classified))
    return {"classified_clauses": classified}


def mock_flag_node(state: PipelineState) -> dict:
    """Mock risk scoring using keyword heuristics."""
    flagged = state.get("flagged_clauses", [])
    logger.info(
        "[MOCK] Step 4/5: Scoring risk for %d clauses",
        len(flagged),
    )

    updated: list[FlaggedClause] = []
    for item in flagged:
        risk = _score_risk(item.clause.chunk.text)
        ct = item.clause.clause_type.value
        reasoning = (
            f"Based on analysis of clause language patterns, "
            f"this {ct} clause has been assessed as "
            f"{risk.value} risk."
        )
        if risk == RiskLevel.HIGH:
            reasoning += (
                " The language contains aggressive or heavily "
                "one-sided terms that could be unfavorable."
            )
        elif risk == RiskLevel.LOW:
            reasoning += (
                " The terms appear balanced and consistent "
                "with standard contract language."
            )
        else:
            reasoning += (
                " Some provisions are broader than typical "
                "and warrant careful review."
            )

        updated.append(FlaggedClause(
            clause=item.clause,
            benchmark=item.benchmark,
            risk_level=risk,
            risk_reasoning=reasoning,
        ))

    return {"flagged_clauses": updated}


def mock_explain_node(state: PipelineState) -> dict:
    """Mock explanation generation using templates."""
    flagged = state.get("flagged_clauses", [])
    logger.info(
        "[MOCK] Step 5/5: Generating explanations for %d clauses",
        len(flagged),
    )

    explained: list[ExplainedClause] = []
    for item in flagged:
        key = (item.clause.clause_type, item.risk_level)
        mock = _MOCK_EXPLANATIONS.get(key)

        if mock:
            summary = mock["summary"]
            action = mock["action"]
        else:
            ct = item.clause.clause_type.value
            rl = item.risk_level.value
            summary = (
                f"This {ct} clause has been assessed as "
                f"{rl} risk. Review the original text "
                f"for details."
            )
            action = "Review this clause carefully before signing."

        explained.append(ExplainedClause(
            flagged=item,
            plain_english_summary=summary,
            recommended_action=action,
        ))

    return {"explained_clauses": explained}
