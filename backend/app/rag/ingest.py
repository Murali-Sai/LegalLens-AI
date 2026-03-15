"""Ingest legal clause seed data into ChromaDB collections.

Usage:
    python -m app.rag.ingest              # Ingest all seed data
    python -m app.rag.ingest --reset      # Clear collections first, then ingest
"""

import json
import logging
import sys
from pathlib import Path

from app.rag.vector_store import get_collection, initialize_vector_store

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "clause_database"


def load_clauses(filename: str) -> list[dict]:
    """Load clause data from a JSON file."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        logger.error("Clause file not found: %s", filepath)
        return []
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def ingest_clauses(collection_name: str, clauses: list[dict]) -> int:
    """Ingest clauses into a ChromaDB collection. Returns count of added documents."""
    if not clauses:
        return 0

    collection = get_collection(collection_name)

    # Check existing count to avoid duplicates
    existing = collection.count()
    if existing > 0:
        logger.info("Collection '%s' already has %d documents — skipping", collection_name, existing)
        return 0

    ids = []
    documents = []
    metadatas = []

    for i, clause in enumerate(clauses):
        clause_id = f"{collection_name}_{clause['clause_type']}_{i}"
        ids.append(clause_id)
        documents.append(clause["text"])
        metadatas.append({
            "clause_type": clause["clause_type"],
            "doc_type": clause.get("doc_type", "general"),
            "risk_level": clause.get("risk_level", "unknown"),
            "notes": clause.get("notes", ""),
        })

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

    logger.info("Ingested %d clauses into '%s'", len(ids), collection_name)
    return len(ids)


def reset_collections():
    """Delete and recreate both collections."""
    from app.rag.vector_store import get_client

    client = get_client()
    for name in ("standard_clauses", "risky_clauses"):
        try:
            client.delete_collection(name)
            logger.info("Deleted collection '%s'", name)
        except Exception:
            pass
    initialize_vector_store()


def run_ingestion(reset: bool = False):
    """Run the full ingestion pipeline."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    initialize_vector_store()

    if reset:
        logger.info("Resetting collections...")
        reset_collections()

    # Load seed data
    standard = load_clauses("standard_clauses.json")
    risky = load_clauses("risky_clauses.json")

    logger.info("Loaded %d standard clauses, %d risky clauses", len(standard), len(risky))

    # Ingest
    std_count = ingest_clauses("standard_clauses", standard)
    risky_count = ingest_clauses("risky_clauses", risky)

    total = std_count + risky_count
    if total > 0:
        logger.info("Ingestion complete: %d total clauses added", total)
    else:
        logger.info("No new clauses added (collections already populated)")

    # Print summary
    std_col = get_collection("standard_clauses")
    risky_col = get_collection("risky_clauses")
    logger.info("Collection counts — standard: %d, risky: %d", std_col.count(), risky_col.count())


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    run_ingestion(reset=reset_flag)
