"""ChromaDB vector store for legal clause benchmarking."""

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings

_client: chromadb.ClientAPI | None = None


def get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def initialize_vector_store():
    """Ensure collections exist on startup."""
    client = get_client()
    client.get_or_create_collection(
        name="standard_clauses",
        metadata={"description": "Standard/fair legal clause examples for benchmarking"},
    )
    client.get_or_create_collection(
        name="risky_clauses",
        metadata={"description": "Known risky/aggressive legal clause examples"},
    )


def get_collection(name: str):
    return get_client().get_or_create_collection(name=name)
