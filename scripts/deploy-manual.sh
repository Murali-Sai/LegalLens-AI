#!/usr/bin/env bash
# Manual deployment script (alternative to CI/CD)
# Use this to deploy directly from your machine
#
# Usage:
#   chmod +x scripts/deploy-manual.sh
#   ./scripts/deploy-manual.sh <your-gcp-project-id>

set -euo pipefail

PROJECT_ID="${1:?Usage: ./deploy-manual.sh <gcp-project-id>}"
REGION="us-central1"
TAG="$(date +%Y%m%d-%H%M%S)"
BACKEND_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/legallens/backend:$TAG"
FRONTEND_IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/legallens/frontend:$TAG"

echo "=== Deploying LegalLens to GCP Cloud Run ==="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo "Tag:     $TAG"

# Configure Docker
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# Build and push backend
echo ""
echo "--- Building backend ---"
docker build -t "$BACKEND_IMAGE" ./backend
docker push "$BACKEND_IMAGE"

# Build and push frontend
echo ""
echo "--- Building frontend ---"
docker build -t "$FRONTEND_IMAGE" ./frontend
docker push "$FRONTEND_IMAGE"

# Deploy backend
echo ""
echo "--- Deploying backend ---"
gcloud run deploy legallens-backend \
  --image "$BACKEND_IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 120 \
  --min-instances 0 \
  --max-instances 3 \
  --set-env-vars "OPENAI_API_KEY=$(grep OPENAI_API_KEY backend/.env | cut -d= -f2)"

BACKEND_URL=$(gcloud run services describe legallens-backend --region "$REGION" --format 'value(status.url)')

# Deploy frontend
echo ""
echo "--- Deploying frontend ---"
gcloud run deploy legallens-frontend \
  --image "$FRONTEND_IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2

FRONTEND_URL=$(gcloud run services describe legallens-frontend --region "$REGION" --format 'value(status.url)')

echo ""
echo "=== Deployment complete ==="
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo "Health:   $BACKEND_URL/api/health"
