#!/bin/bash
# ChronoLab deploy — the ONE command the account owner runs after bootstrap.sh.
# Builds the backend image, ships it to the EC2 box over SSH, and pushes a fresh
# frontend build to Amplify. Safe to re-run any time you want to push changes —
# it doesn't touch infrastructure, only application code (that's bootstrap.sh's job).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env not found. Run scripts/bootstrap.sh first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

require_var() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "ERROR: $name is empty in .env — run scripts/bootstrap.sh first." >&2
    exit 1
  fi
}

if [ "${AWS_MODE:-local}" != "cloud" ]; then
  echo "ERROR: deploy.sh only makes sense with AWS_MODE=cloud (nothing to deploy to in local mode)." >&2
  exit 1
fi

require_var EC2_PUBLIC_DNS
require_var EC2_SSH_KEY_PATH
require_var AMPLIFY_APP_ID

for tool in docker ssh scp zip; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: $tool not found on PATH — required for deploy.sh." >&2
    exit 1
  fi
done

# ── Backend: build -> docker save -> scp -> ssh load+compose up ────────────

echo "== Building backend image =="
docker build -f "$REPO_ROOT/backend/Dockerfile" -t chronolab-backend:latest "$REPO_ROOT"

echo "== Shipping image to EC2 ($EC2_PUBLIC_DNS) =="
IMAGE_TAR="$(mktemp).tar"
docker save chronolab-backend:latest -o "$IMAGE_TAR"

SSH_OPTS=(-i "$EC2_SSH_KEY_PATH" -o StrictHostKeyChecking=accept-new)
REMOTE="ec2-user@${EC2_PUBLIC_DNS}"

ssh "${SSH_OPTS[@]}" "$REMOTE" "mkdir -p ~/chronolab"
scp "${SSH_OPTS[@]}" "$IMAGE_TAR" "$REMOTE:~/chronolab/chronolab-backend.tar"
scp "${SSH_OPTS[@]}" "$REPO_ROOT/deploy/docker-compose.yml" "$REPO_ROOT/deploy/Caddyfile" "$REMOTE:~/chronolab/"
scp "${SSH_OPTS[@]}" "$ENV_FILE" "$REMOTE:~/chronolab/.env"

ssh "${SSH_OPTS[@]}" "$REMOTE" "cd ~/chronolab && \
  docker load -i chronolab-backend.tar && \
  rm -f chronolab-backend.tar && \
  docker compose up -d"

rm -f "$IMAGE_TAR"
echo "Backend deployed. Health check:"
curl -s -o /dev/null -w "  http://%{url_effective} -> %{http_code}\n" "http://${EC2_PUBLIC_DNS}/" || true

# ── Frontend: build -> Amplify manual deployment ────────────────────────────

echo "== Building frontend =="
(cd "$REPO_ROOT/frontend" && npm install && npm run build)

echo "== Deploying to Amplify (app $AMPLIFY_APP_ID) =="
DEPLOY_ZIP="$(mktemp).zip"
(cd "$REPO_ROOT/frontend/dist" && zip -qr "$DEPLOY_ZIP" .)

DEPLOYMENT=$(aws amplify create-deployment --app-id "$AMPLIFY_APP_ID" --branch-name main)
JOB_ID=$(echo "$DEPLOYMENT" | python3 -c "import json,sys; print(json.load(sys.stdin)['jobId'])" 2>/dev/null || \
         echo "$DEPLOYMENT" | python -c "import json,sys; print(json.load(sys.stdin)['jobId'])")
ZIP_UPLOAD_URL=$(echo "$DEPLOYMENT" | python3 -c "import json,sys; print(json.load(sys.stdin)['zipUploadUrl'])" 2>/dev/null || \
         echo "$DEPLOYMENT" | python -c "import json,sys; print(json.load(sys.stdin)['zipUploadUrl'])")

curl -s -X PUT -H "Content-Type: application/zip" --data-binary "@${DEPLOY_ZIP}" "$ZIP_UPLOAD_URL" >/dev/null
aws amplify start-deployment --app-id "$AMPLIFY_APP_ID" --branch-name main --job-id "$JOB_ID" >/dev/null

rm -f "$DEPLOY_ZIP"
echo "Frontend deployment started (job $JOB_ID)."
echo "  https://main.${AMPLIFY_DEFAULT_DOMAIN:-<unknown>}"
echo ""
echo "== deploy.sh complete =="
