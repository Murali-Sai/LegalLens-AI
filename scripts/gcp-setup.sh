#!/usr/bin/env bash
# GCP setup script for LegalLens deployment
# Run once to configure your GCP project for Cloud Run deployment
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - A GCP project created
#
# Usage:
#   chmod +x scripts/gcp-setup.sh
#   ./scripts/gcp-setup.sh <your-gcp-project-id>

set -euo pipefail

PROJECT_ID="${1:?Usage: ./gcp-setup.sh <gcp-project-id>}"
REGION="us-central1"
REPO_NAME="legallens"

echo "=== Setting up GCP project: $PROJECT_ID ==="

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Create Artifact Registry repo
echo "Creating Artifact Registry repository..."
gcloud artifacts repositories create "$REPO_NAME" \
  --repository-format=docker \
  --location="$REGION" \
  --description="LegalLens container images" \
  2>/dev/null || echo "Repository already exists"

# Create service account for GitHub Actions
SA_NAME="github-actions-deploy"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

echo "Creating service account..."
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="GitHub Actions Deploy" \
  2>/dev/null || echo "Service account already exists"

# Grant required roles
echo "Granting roles..."
for ROLE in \
  roles/run.admin \
  roles/artifactregistry.writer \
  roles/iam.serviceAccountUser \
  roles/storage.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE" \
    --quiet
done

# Generate key
KEY_FILE="gcp-sa-key.json"
echo "Generating service account key..."
gcloud iam service-accounts keys create "$KEY_FILE" \
  --iam-account="$SA_EMAIL"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "1. Add these GitHub repository secrets:"
echo "   GCP_PROJECT_ID = $PROJECT_ID"
echo "   GCP_SA_KEY     = (contents of $KEY_FILE)"
echo "   ANTHROPIC_API_KEY = (your Anthropic API key)"
echo ""
echo "2. Delete the key file after adding to GitHub:"
echo "   rm $KEY_FILE"
echo ""
echo "3. Push to main to trigger deployment:"
echo "   git push origin main"
