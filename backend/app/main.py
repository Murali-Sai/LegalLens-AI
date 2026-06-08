import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.rag.vector_store import initialize_vector_store

# Directory holding the built React app (populated by the Docker build).
# Absent during local backend-only dev — the SPA is then served by Vite.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

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
            "OPENAI_API_KEY not set — running in mock mode (keyword-based analysis)"
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


# ─── Serve the built React SPA (single-container deploy, e.g. HF Spaces) ──────
# Registered AFTER the API router so /api/* always takes precedence.
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/")
    async def _serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def _serve_spa(full_path: str):
        # Never let the SPA fallback swallow unmatched API routes
        if full_path.startswith("api"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        # Client-side routing fallback
        return FileResponse(STATIC_DIR / "index.html")
else:
    logger.info("No static/ dir found — running API-only (frontend served separately)")
