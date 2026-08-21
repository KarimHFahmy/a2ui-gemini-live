#!/usr/bin/env bash
#
# Deploys the demo to Cloud Run.
#
# Everything is one container and one service. Vertex AI is reached with the
# runtime service account's own credentials, so no key material is built into
# the image or stored in Secret Manager.
#
#   ./deploy/deploy.sh
#
# Override anything via the environment:
#   PROJECT_ID=my-project REGION=europe-west4 ./deploy/deploy.sh

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-europe-west4}"
SERVICE="${SERVICE:-adaptive-advisory}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-${SERVICE}-sa}"

# Live API region availability differs from Cloud Run's. Keeping the model
# location separate lets the service run close to German users while the model
# call goes wherever the Live API is actually served.
MODEL_LOCATION="${MODEL_LOCATION:-us-central1}"
MODEL="${GEMINI_LIVE_MODEL:-gemini-live-2.5-flash-native-audio}"
VOICE="${LIVE_VOICE_NAME:-Aoede}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "PROJECT_ID is not set and gcloud has no default project." >&2
  exit 1
fi

SA_EMAIL="${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "==> Project ${PROJECT_ID}, region ${REGION}, service ${SERVICE}"

echo "==> Enabling required APIs"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  --project "${PROJECT_ID}"

if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project "${PROJECT_ID}" &>/dev/null; then
  echo "==> Creating runtime service account ${SA_EMAIL}"
  gcloud iam service-accounts create "${SERVICE_ACCOUNT}" \
    --display-name "Adaptive Advisory Cloud Run runtime" \
    --project "${PROJECT_ID}"
fi

echo "==> Granting Vertex AI access"
# roles/aiplatform.user is the least privilege that covers a Live API session.
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:${SA_EMAIL}" \
  --role roles/aiplatform.user \
  --condition=None \
  --quiet >/dev/null

echo "==> Deploying"
gcloud run deploy "${SERVICE}" \
  --source . \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --service-account "${SA_EMAIL}" \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 2 \
  --memory 1Gi \
  --concurrency 12 \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 3600 \
  --session-affinity \
  --set-env-vars "USE_VERTEX_AI=true,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION},GEMINI_LIVE_MODEL=${MODEL},LIVE_LANGUAGE_CODE=de-DE,LIVE_VOICE_NAME=${VOICE},LOG_LEVEL=INFO"

URL="$(gcloud run services describe "${SERVICE}" \
  --project "${PROJECT_ID}" --region "${REGION}" --format 'value(status.url)')"

echo
echo "==> Live at ${URL}"
echo "    Health:  ${URL}/healthz"
echo "    Preview: ${URL}/preview.html  (catalog without a voice session)"
