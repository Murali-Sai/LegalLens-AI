FROM python:3.11-slim AS base

WORKDIR /app

# System deps: libmagic for filetype detection (unstructured), curl for healthcheck.
# PDF text is extracted via PyMuPDF (no poppler/tesseract/libreoffice needed).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (cached layer)
COPY pyproject.toml .
RUN pip install --no-cache-dir "." && \
    pip install --no-cache-dir nltk && \
    python -c "import nltk; nltk.download('punkt_tab', quiet=True); nltk.download('averaged_perceptron_tagger_eng', quiet=True)" && \
    python -m spacy download en_core_web_sm
# ^ unstructured uses spaCy for sentence tokenization; pre-install the model.

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /app/data/chroma_db /app/mlruns

ENV PYTHONUNBUFFERED=1
ENV CHROMA_PERSIST_DIR=/app/data/chroma_db
ENV MLFLOW_TRACKING_URI=/app/mlruns

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
