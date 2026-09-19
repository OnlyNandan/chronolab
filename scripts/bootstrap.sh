#!/bin/bash
# ChronoLab bootstrap script — the ONLY infrastructure-provisioning entry point.
#
# Run by the account owner after filling in the top block of .env:
#   cp .env.example .env && $EDITOR .env && ./scripts/bootstrap.sh
#
# Idempotent: safe to re-run after a partial failure. Every step checks
# before it creates. Appends generated resource identifiers to .env.
#
# Each phase of MIGRATION_PLAN.md appends its own provisioning block below,
# guarded so the script stays idempotent end to end.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

# ── Preflight ──────────────────────────────────────────────────────────────

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env not found. Run: cp .env.example .env && \$EDITOR .env" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

require_var() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "ERROR: required variable $name is empty in .env" >&2
    exit 1
  fi
}

# Idempotent .env upsert: replaces the line if the key exists, appends otherwise.
upsert_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    local tmp
    tmp="$(mktemp)"
    awk -F= -v k="$key" -v v="$value" 'BEGIN{OFS="="} $1==k{$0=k"="v} {print}' "$ENV_FILE" > "$tmp"
    mv "$tmp" "$ENV_FILE"
  else
    echo "${key}=${value}" >> "$ENV_FILE"
  fi
  export "${key}=${value}"
}

require_var AWS_REGION
require_var RESOURCE_SUFFIX

echo "== ChronoLab bootstrap =="
echo "AWS_MODE=${AWS_MODE:-local}"

AWS_CLI_ARGS=()
if [ "${AWS_MODE:-local}" = "cloud" ]; then
  require_var BEDROCK_REGION

  if ! command -v aws >/dev/null 2>&1; then
    echo "ERROR: AWS CLI not found on PATH." >&2
    exit 1
  fi

  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "ERROR: 'aws sts get-caller-identity' failed. Run 'aws configure' first." >&2
    exit 1
  fi

  echo "Preflight OK — AWS CLI present, credentials valid."

  BEDROCK_TEXT_MODEL_ID="${BEDROCK_TEXT_MODEL_ID:-anthropic.claude-3-5-haiku-20241022-v1:0}"
  echo "Checking Bedrock model access for $BEDROCK_TEXT_MODEL_ID in $BEDROCK_REGION..."
  if ! aws bedrock-runtime converse \
        --region "$BEDROCK_REGION" \
        --model-id "$BEDROCK_TEXT_MODEL_ID" \
        --messages '[{"role":"user","content":[{"text":"ping"}]}]' \
        >/dev/null 2>&1; then
    echo "ERROR: Bedrock model access check failed for $BEDROCK_TEXT_MODEL_ID in $BEDROCK_REGION." >&2
    echo "  Request model access in the Bedrock console (Model access page) and re-run this script." >&2
    exit 1
  fi
  echo "Bedrock model access confirmed."
else
  export AWS_ACCESS_KEY_ID="test"
  export AWS_SECRET_ACCESS_KEY="test"
  LOCALSTACK_ENDPOINT_URL="${LOCALSTACK_ENDPOINT_URL:-http://localhost:4566}"
  AWS_CLI_ARGS=(--endpoint-url "$LOCALSTACK_ENDPOINT_URL")
  echo "AWS_MODE=local — targeting LocalStack/moto_server at $LOCALSTACK_ENDPOINT_URL."

  if ! curl -s -o /dev/null "$LOCALSTACK_ENDPOINT_URL"; then
    echo "ERROR: nothing responding at $LOCALSTACK_ENDPOINT_URL. Start moto_server first." >&2
    exit 1
  fi
fi

# ── Phase 1: S3 bucket + DynamoDB table ─────────────────────────────────────

BUCKET_NAME="chronolab-pdfs-${RESOURCE_SUFFIX}"
TABLE_NAME="chronolab-records-${RESOURCE_SUFFIX}"

if aws s3api head-bucket --bucket "$BUCKET_NAME" "${AWS_CLI_ARGS[@]}" >/dev/null 2>&1; then
  echo "S3 bucket $BUCKET_NAME already exists."
else
  echo "Creating S3 bucket $BUCKET_NAME..."
  if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION" "${AWS_CLI_ARGS[@]}" >/dev/null
  else
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION" \
      --create-bucket-configuration LocationConstraint="$AWS_REGION" "${AWS_CLI_ARGS[@]}" >/dev/null
  fi
  aws s3api put-public-access-block --bucket "$BUCKET_NAME" "${AWS_CLI_ARGS[@]}" \
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" "${AWS_CLI_ARGS[@]}" \
    --versioning-configuration Status=Enabled
  echo "Bucket created (public access blocked, versioning enabled)."
fi
upsert_env "S3_BUCKET_NAME" "$BUCKET_NAME"

if aws dynamodb describe-table --table-name "$TABLE_NAME" "${AWS_CLI_ARGS[@]}" >/dev/null 2>&1; then
  echo "DynamoDB table $TABLE_NAME already exists."
else
  echo "Creating DynamoDB table $TABLE_NAME..."
  aws dynamodb create-table --table-name "$TABLE_NAME" "${AWS_CLI_ARGS[@]}" \
    --attribute-definitions AttributeName=patient_id,AttributeType=S AttributeName=record_id,AttributeType=S \
    --key-schema AttributeName=patient_id,KeyType=HASH AttributeName=record_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST >/dev/null
  aws dynamodb wait table-exists --table-name "$TABLE_NAME" "${AWS_CLI_ARGS[@]}"
  echo "Table created (on-demand billing)."
fi
upsert_env "DYNAMODB_TABLE_NAME" "$TABLE_NAME"

echo "== bootstrap.sh complete =="
echo "S3_BUCKET_NAME=$BUCKET_NAME"
echo "DYNAMODB_TABLE_NAME=$TABLE_NAME"
echo "Next: run the app (backend + frontend) or scripts/deploy.sh once it exists."
