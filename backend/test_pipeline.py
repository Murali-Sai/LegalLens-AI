"""Quick test script for the pipeline."""
import asyncio
import sys
import traceback

from app.pipeline.graph import run_analysis


async def test():
    with open("data/sample_contracts/test_agreement.docx", "rb") as f:
        data = f.read()
    try:
        result = await run_analysis("test-001", "test_agreement.docx", data)
        print(f"SUCCESS: {result.total_clauses} clauses found")
        print(f"High: {result.high_risk_count}, Medium: {result.medium_risk_count}, Low: {result.low_risk_count}")
        for c in result.clauses:
            rl = c.flagged.risk_level.value.upper()
            ct = c.flagged.clause.clause_type.value
            print(f"  [{rl}] {ct}: {c.plain_english_summary[:100]}...")
    except Exception as e:
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
