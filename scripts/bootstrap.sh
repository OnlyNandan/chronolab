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

# AWS CLI + real credentials are required even in AWS_MODE=local: Cognito and
# Verified Permissions have no LocalStack/moto emulation, so Phase 3 always talks
# to the real account regardless of which mode S3/DynamoDB/Bedrock are in
# (see MIGRATION_PLAN.md's hour-12 fallback — this is deliberate).
if ! command -v aws >/dev/null 2>&1; then
  echo "ERROR: AWS CLI not found on PATH." >&2
  exit 1
fi

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "ERROR: 'aws sts get-caller-identity' failed. Run 'aws configure' first." >&2
  exit 1
fi

echo "Preflight OK — AWS CLI present, credentials valid."

# S3_DDB_ENV scopes the LocalStack test credentials to ONLY the S3/DynamoDB calls
# below via `env`, never `export` — Cognito/AVP later in this script must keep
# using the real credential chain from `aws configure`, even in AWS_MODE=local.
AWS_CLI_ARGS=()
S3_DDB_ENV=()
if [ "${AWS_MODE:-local}" = "cloud" ]; then
  require_var BEDROCK_REGION

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
  LOCALSTACK_ENDPOINT_URL="${LOCALSTACK_ENDPOINT_URL:-http://localhost:4566}"
  AWS_CLI_ARGS=(--endpoint-url "$LOCALSTACK_ENDPOINT_URL")
  S3_DDB_ENV=(AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test)
  echo "AWS_MODE=local — S3/DynamoDB target LocalStack/moto_server at $LOCALSTACK_ENDPOINT_URL."
  echo "Cognito/AVP below still target the real account — there is no local emulation for them."

  if ! curl -s -o /dev/null "$LOCALSTACK_ENDPOINT_URL"; then
    echo "ERROR: nothing responding at $LOCALSTACK_ENDPOINT_URL. Start moto_server first." >&2
    exit 1
  fi
fi

# ── Phase 1: S3 bucket + DynamoDB table ─────────────────────────────────────

BUCKET_NAME="chronolab-pdfs-${RESOURCE_SUFFIX}"
TABLE_NAME="chronolab-records-${RESOURCE_SUFFIX}"

if env "${S3_DDB_ENV[@]}" aws s3api head-bucket --bucket "$BUCKET_NAME" "${AWS_CLI_ARGS[@]}" >/dev/null 2>&1; then
  echo "S3 bucket $BUCKET_NAME already exists."
else
  echo "Creating S3 bucket $BUCKET_NAME..."
  if [ "$AWS_REGION" = "us-east-1" ]; then
    env "${S3_DDB_ENV[@]}" aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION" "${AWS_CLI_ARGS[@]}" >/dev/null
  else
    env "${S3_DDB_ENV[@]}" aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION" \
      --create-bucket-configuration LocationConstraint="$AWS_REGION" "${AWS_CLI_ARGS[@]}" >/dev/null
  fi
  env "${S3_DDB_ENV[@]}" aws s3api put-public-access-block --bucket "$BUCKET_NAME" "${AWS_CLI_ARGS[@]}" \
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  env "${S3_DDB_ENV[@]}" aws s3api put-bucket-versioning --bucket "$BUCKET_NAME" "${AWS_CLI_ARGS[@]}" \
    --versioning-configuration Status=Enabled
  echo "Bucket created (public access blocked, versioning enabled)."
fi
upsert_env "S3_BUCKET_NAME" "$BUCKET_NAME"

if env "${S3_DDB_ENV[@]}" aws dynamodb describe-table --table-name "$TABLE_NAME" "${AWS_CLI_ARGS[@]}" >/dev/null 2>&1; then
  echo "DynamoDB table $TABLE_NAME already exists."
else
  echo "Creating DynamoDB table $TABLE_NAME..."
  env "${S3_DDB_ENV[@]}" aws dynamodb create-table --table-name "$TABLE_NAME" "${AWS_CLI_ARGS[@]}" \
    --attribute-definitions AttributeName=patient_id,AttributeType=S AttributeName=record_id,AttributeType=S \
    --key-schema AttributeName=patient_id,KeyType=HASH AttributeName=record_id,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST >/dev/null
  env "${S3_DDB_ENV[@]}" aws dynamodb wait table-exists --table-name "$TABLE_NAME" "${AWS_CLI_ARGS[@]}"
  echo "Table created (on-demand billing)."
fi
upsert_env "DYNAMODB_TABLE_NAME" "$TABLE_NAME"

# ── Phase 3: Cognito user pool + Verified Permissions policy store ─────────

PYTHON_BIN="python3"
command -v python3 >/dev/null 2>&1 || PYTHON_BIN="python"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: neither python3 nor python found on PATH (needed to JSON-encode Cedar policy text)." >&2
  exit 1
fi

require_var COGNITO_DOCTOR_USERNAME
require_var COGNITO_DOCTOR_PASSWORD
require_var COGNITO_PATIENT_USERNAME
require_var COGNITO_PATIENT_PASSWORD
require_var COGNITO_PATIENT_ID

CEDAR_DIR="$REPO_ROOT/cedar"
POOL_NAME="chronolab-users-${RESOURCE_SUFFIX}"

if [ -n "${COGNITO_USER_POOL_ID:-}" ]; then
  echo "Cognito user pool already recorded in .env: $COGNITO_USER_POOL_ID"
else
  echo "Creating Cognito user pool $POOL_NAME..."
  COGNITO_USER_POOL_ID=$(aws cognito-idp create-user-pool \
    --pool-name "$POOL_NAME" \
    --auto-verified-attributes email \
    --schema Name=role,AttributeDataType=String,Mutable=true Name=patient_id,AttributeDataType=String,Mutable=true \
    --query 'UserPool.Id' --output text)
  echo "Created user pool $COGNITO_USER_POOL_ID"
fi
upsert_env "COGNITO_USER_POOL_ID" "$COGNITO_USER_POOL_ID"

if [ -n "${COGNITO_APP_CLIENT_ID:-}" ]; then
  echo "Cognito app client already recorded in .env: $COGNITO_APP_CLIENT_ID"
else
  echo "Creating Cognito app client..."
  COGNITO_APP_CLIENT_ID=$(aws cognito-idp create-user-pool-client \
    --user-pool-id "$COGNITO_USER_POOL_ID" \
    --client-name chronolab-web \
    --no-generate-secret \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH ALLOW_ADMIN_USER_PASSWORD_AUTH \
    --read-attributes email "custom:role" "custom:patient_id" \
    --write-attributes email "custom:role" "custom:patient_id" \
    --query 'UserPoolClient.ClientId' --output text)
  echo "Created app client $COGNITO_APP_CLIENT_ID"
fi
upsert_env "COGNITO_APP_CLIENT_ID" "$COGNITO_APP_CLIENT_ID"

# Duplicated with the VITE_ prefix so the frontend build can read them —
# Vite only exposes env vars prefixed VITE_ to browser code.
upsert_env "VITE_AWS_REGION" "$AWS_REGION"
upsert_env "VITE_COGNITO_USER_POOL_ID" "$COGNITO_USER_POOL_ID"
upsert_env "VITE_COGNITO_APP_CLIENT_ID" "$COGNITO_APP_CLIENT_ID"

create_or_update_user() {
  local username="$1" password="$2" role="$3" patient_id="$4"
  if aws cognito-idp admin-get-user --user-pool-id "$COGNITO_USER_POOL_ID" --username "$username" >/dev/null 2>&1; then
    echo "Cognito user $username already exists."
  else
    echo "Creating Cognito user $username (role=$role)..."
    aws cognito-idp admin-create-user \
      --user-pool-id "$COGNITO_USER_POOL_ID" \
      --username "$username" \
      --user-attributes Name=email,Value="$username" Name=email_verified,Value=true \
                         Name="custom:role",Value="$role" Name="custom:patient_id",Value="$patient_id" \
      --message-action SUPPRESS >/dev/null
  fi
  aws cognito-idp admin-set-user-password \
    --user-pool-id "$COGNITO_USER_POOL_ID" \
    --username "$username" \
    --password "$password" \
    --permanent >/dev/null
}

create_or_update_user "$COGNITO_DOCTOR_USERNAME" "$COGNITO_DOCTOR_PASSWORD" "doctor" ""
create_or_update_user "$COGNITO_PATIENT_USERNAME" "$COGNITO_PATIENT_PASSWORD" "patient" "$COGNITO_PATIENT_ID"
echo "Cognito test users ready (passwords set from .env)."

if [ -n "${AVP_POLICY_STORE_ID:-}" ]; then
  echo "AVP policy store already recorded in .env: $AVP_POLICY_STORE_ID"
else
  echo "Creating Verified Permissions policy store (non-validating)..."
  AVP_POLICY_STORE_ID=$(aws verifiedpermissions create-policy-store \
    --validation-settings mode=OFF \
    --description "ChronoLab ${RESOURCE_SUFFIX}" \
    --query 'policyStoreId' --output text)
  echo "Created policy store $AVP_POLICY_STORE_ID"
fi
upsert_env "AVP_POLICY_STORE_ID" "$AVP_POLICY_STORE_ID"

if [ -n "${AVP_IDENTITY_SOURCE_ID:-}" ]; then
  echo "AVP identity source already recorded in .env: $AVP_IDENTITY_SOURCE_ID"
else
  ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
  USER_POOL_ARN="arn:aws:cognito-idp:${AWS_REGION}:${ACCOUNT_ID}:userpool/${COGNITO_USER_POOL_ID}"
  echo "Creating AVP identity source for $USER_POOL_ARN..."
  AVP_IDENTITY_SOURCE_ID=$(aws verifiedpermissions create-identity-source \
    --policy-store-id "$AVP_POLICY_STORE_ID" \
    --configuration "{\"cognitoUserPoolConfiguration\":{\"userPoolArn\":\"${USER_POOL_ARN}\",\"clientIds\":[\"${COGNITO_APP_CLIENT_ID}\"]}}" \
    --principal-entity-type "ChronoLab::User" \
    --query 'identitySourceId' --output text)
  echo "Created identity source $AVP_IDENTITY_SOURCE_ID"
fi
upsert_env "AVP_IDENTITY_SOURCE_ID" "$AVP_IDENTITY_SOURCE_ID"

create_or_update_policy() {
  local var_name="$1" cedar_file="$2" description="$3"
  local existing_id="${!var_name:-}"
  if [ -n "$existing_id" ]; then
    echo "AVP policy '$description' already recorded in .env: $existing_id"
    return
  fi
  echo "Loading AVP policy '$description' from $cedar_file..."
  # Read the .cedar file directly with explicit UTF-8 (not via a bash stdin pipe —
  # on Windows that silently mis-decodes non-ASCII characters like the em-dashes
  # in these files' comments, corrupting the policy statement sent to AVP).
  local statement_json
  statement_json="$("$PYTHON_BIN" -c "
import json, sys
with open(sys.argv[1], 'r', encoding='utf-8') as f:
    print(json.dumps(f.read()))
" "$cedar_file")"
  local policy_id
  policy_id=$(aws verifiedpermissions create-policy \
    --policy-store-id "$AVP_POLICY_STORE_ID" \
    --definition "{\"static\":{\"description\":\"${description}\",\"statement\":${statement_json}}}" \
    --query 'policyId' --output text)
  upsert_env "$var_name" "$policy_id"
  echo "Created policy $policy_id"
}

create_or_update_policy "AVP_DOCTOR_POLICY_ID" "$CEDAR_DIR/doctor.cedar" "ChronoLab doctor policy"
create_or_update_policy "AVP_PATIENT_POLICY_ID" "$CEDAR_DIR/patient.cedar" "ChronoLab patient policy"

echo "== bootstrap.sh complete =="
echo "S3_BUCKET_NAME=$BUCKET_NAME"
echo "DYNAMODB_TABLE_NAME=$TABLE_NAME"
echo "COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID"
echo "COGNITO_APP_CLIENT_ID=$COGNITO_APP_CLIENT_ID"
echo "AVP_POLICY_STORE_ID=$AVP_POLICY_STORE_ID"
echo ""
echo "Test logins:"
echo "  Doctor:  $COGNITO_DOCTOR_USERNAME / (password from .env)"
echo "  Patient: $COGNITO_PATIENT_USERNAME / (password from .env), patient_id=$COGNITO_PATIENT_ID"
echo ""
echo "If a login succeeds but every API call still 403s with an empty determining_policies"
echo "list: the Cedar policies expect principal.role / principal.patient_id to come from the"
echo "Cognito custom:role / custom:patient_id token claims automatically. That mapping is"
echo "standard AVP+Cognito identity-source behavior but has never been exercised against a"
echo "real pool in this project — if it doesn't show up, check the decoded ID token's claims"
echo "(jwt.io) match what the AVP console's 'test bench' expects for the identity source."
echo ""
echo "Next: run the app (backend + frontend) or scripts/deploy.sh once it exists."
