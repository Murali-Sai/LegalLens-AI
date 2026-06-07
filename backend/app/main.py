import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.rag.vector_store import initialize_vector_store

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown."""
    logger.info("Starting LegalLens API...")

    from app.db import init_db
    init_db()

    initialize_vector_store()
    from app.rag.ingest import run_ingestion
    run_ingestion()

    if settings.effective_mock_mode:
        logger.warning(
            "ANTHROPIC_API_KEY not set — running in mock mode (keyword-based analysis)"
        )

    logger.info("LegalLens API ready")
    yield
    logger.info("Shutting down LegalLens API")


app = FastAPI(
    title="LegalLens API",
    description="AI-powered Legal Document Analyst Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
