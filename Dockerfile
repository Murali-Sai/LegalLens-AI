# ─────────────────────────────────────────────────────────────────────────────
# Single-container build for Hugging Face Spaces (Docker SDK).
# Stage 1 builds the React frontend; stage 2 runs FastAPI, which also serves
# the built frontend as static files. Listens on port 7860 (HF default).
# ─────────────────────────────────────────────────────────────────────────────

# Stage 1: build the React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci 2>/dev/null || npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: backend + static serving
FROM python:3.11-slim

# System deps: libmagic for filetype detection (unstructured), curl for healthcheck.
# PDF text is extracted via PyMuPDF (no poppler/tesseract/libreoffice needed).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces runs containers as UID 1000 — create a matching non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    CHROMA_PERSIST_DIR=/home/user/app/data/chroma_db \
    MLFLOW_TRACKING_URI=/home/user/app/mlruns

WORKDIR /home/user/app

# Install Python dependencies (cached layer)
COPY --chown=user backend/pyproject.toml .
RUN pip install --no-cache-dir --user "." && \
    pip install --no-cache-dir --user nltk && \
    python -c "import nltk; nltk.download('punkt_tab', quiet=True); nltk.download('averaged_perceptron_tagger_eng', quiet=True)" && \
    python -m spacy download en_core_web_sm
# ^ unstructured uses spaCy for sentence tokenization; pre-install the model into
#   the user site-packages so it is never auto-fetched (read-only FS) at runtime.

# Application code
COPY --chown=user backend/ .

# Built frontend → served by FastAPI at /
COPY --chown=user --from=frontend-build /frontend/dist ./static

RUN mkdir -p data/chroma_db mlruns

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
