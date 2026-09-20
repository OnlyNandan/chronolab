#!/bin/bash
# ChronoLab teardown — deletes everything scripts/bootstrap.sh created, in
# reverse order. Safe to re-run: every step checks before it deletes.
#
# Usage: ./scripts/teardown.sh          (asks for confirmation)
#        ./scripts/teardown.sh --yes    (skips confirmation, for scripting)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

PYTHON_BIN="python3"
command -v python3 >/dev/null 2>&1 || PYTHON_BIN="python"

if [ ! -f "$ENV_FILE" ]; then
  echo "ERROR: .env not found — nothing to tear down." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [ "${1:-}" != "--yes" ]; then
  echo "This will PERMANENTLY DELETE the following (if they exist):"
  echo "  EC2 instance:          ${EC2_INSTANCE_ID:-<none>}"
  echo "  Security group:        ${EC2_SECURITY_GROUP_ID:-<none>}"
  echo "  Key pair:               ${EC2_KEY_NAME:-<none>} (and local file ${EC2_SSH_KEY_PATH:-<none>})"
  echo "  IAM role/profile:       chronolab-ec2-role-${RESOURCE_SUFFIX:-<unset>} / chronolab-ec2-profile-${RESOURCE_SUFFIX:-<unset>}"
  echo "  Cognito user pool:      ${COGNITO_USER_POOL_ID:-<none>}"
  echo "  AVP policy store:       ${AVP_POLICY_STORE_ID:-<none>}"
  echo "  DynamoDB table:         ${DYNAMODB_TABLE_NAME:-<none>} (ALL DATA IN IT)"
  echo "  S3 bucket:              ${S3_BUCKET_NAME:-<none>} (ALL FILES IN IT)"
  echo "  Amplify app:            ${AMPLIFY_APP_ID:-<none>}"
  echo ""
  read -r -p "Type 'yes' to confirm: " CONFIRM
  if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted. Nothing was deleted."
    exit 0
  fi
fi

echo "== Tearing down =="

# ── EC2 ──────────────────────────────────────────────────────────────────
if [ -n "${EC2_INSTANCE_ID:-}" ]; then
  echo "Terminating EC2 instance $EC2_INSTANCE_ID..."
  aws ec2 terminate-instances --instance-ids "$EC2_INSTANCE_ID" >/dev/null 2>&1 || true
  aws ec2 wait instance-terminated --instance-ids "$EC2_INSTANCE_ID" 2>/dev/null || true
fi

if [ -n "${EC2_SECURITY_GROUP_ID:-}" ]; then
  echo "Deleting security group $EC2_SECURITY_GROUP_ID..."
  aws ec2 delete-security-group --group-id "$EC2_SECURITY_GROUP_ID" >/dev/null 2>&1 || true
fi

if [ -n "${EC2_KEY_NAME:-}" ]; then
  echo "Deleting key pair $EC2_KEY_NAME..."
  aws ec2 delete-key-pair --key-name "$EC2_KEY_NAME" >/dev/null 2>&1 || true
  if [ -n "${EC2_SSH_KEY_PATH:-}" ] && [ -f "$EC2_SSH_KEY_PATH" ]; then
    rm -f "$EC2_SSH_KEY_PATH"
  fi
fi

# ── IAM ──────────────────────────────────────────────────────────────────
ROLE_NAME="chronolab-ec2-role-${RESOURCE_SUFFIX:-}"
PROFILE_NAME="chronolab-ec2-profile-${RESOURCE_SUFFIX:-}"

if aws iam get-instance-profile --instance-profile-name "$PROFILE_NAME" >/dev/null 2>&1; then
  echo "Removing role from instance profile and deleting $PROFILE_NAME..."
  aws iam remove-role-from-instance-profile --instance-profile-name "$PROFILE_NAME" --role-name "$ROLE_NAME" >/dev/null 2>&1 || true
  aws iam delete-instance-profile --instance-profile-name "$PROFILE_NAME" >/dev/null 2>&1 || true
fi

if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  echo "Deleting IAM role $ROLE_NAME..."
  aws iam delete-role-policy --role-name "$ROLE_NAME" --policy-name "chronolab-least-privilege" >/dev/null 2>&1 || true
  aws iam delete-role --role-name "$ROLE_NAME" >/dev/null 2>&1 || true
fi

# ── Verified Permissions ─────────────────────────────────────────────────
if [ -n "${AVP_POLICY_STORE_ID:-}" ]; then
  for policy_var in AVP_DOCTOR_POLICY_ID AVP_PATIENT_POLICY_ID; do
    policy_id="${!policy_var:-}"
    if [ -n "$policy_id" ]; then
      echo "Deleting AVP policy $policy_id..."
      aws verifiedpermissions delete-policy --policy-store-id "$AVP_POLICY_STORE_ID" \
        --policy-id "$policy_id" >/dev/null 2>&1 || true
    fi
  done

  if [ -n "${AVP_IDENTITY_SOURCE_ID:-}" ]; then
    echo "Deleting AVP identity source $AVP_IDENTITY_SOURCE_ID..."
    aws verifiedpermissions delete-identity-source --policy-store-id "$AVP_POLICY_STORE_ID" \
      --identity-source-id "$AVP_IDENTITY_SOURCE_ID" >/dev/null 2>&1 || true
  fi

  echo "Deleting AVP policy store $AVP_POLICY_STORE_ID..."
  aws verifiedpermissions delete-policy-store --policy-store-id "$AVP_POLICY_STORE_ID" >/dev/null 2>&1 || true
fi

# ── Cognito ──────────────────────────────────────────────────────────────
if [ -n "${COGNITO_USER_POOL_ID:-}" ]; then
  echo "Deleting Cognito user pool $COGNITO_USER_POOL_ID (app client goes with it)..."
  aws cognito-idp delete-user-pool --user-pool-id "$COGNITO_USER_POOL_ID" >/dev/null 2>&1 || true
fi

# ── DynamoDB ─────────────────────────────────────────────────────────────
if [ -n "${DYNAMODB_TABLE_NAME:-}" ]; then
  echo "Deleting DynamoDB table $DYNAMODB_TABLE_NAME..."
  aws dynamodb delete-table --table-name "$DYNAMODB_TABLE_NAME" >/dev/null 2>&1 || true
fi

# ── S3 ───────────────────────────────────────────────────────────────────
if [ -n "${S3_BUCKET_NAME:-}" ]; then
  echo "Emptying and deleting S3 bucket $S3_BUCKET_NAME..."
  aws s3 rm "s3://${S3_BUCKET_NAME}" --recursive >/dev/null 2>&1 || true
  # Versioned buckets need every version deleted, not just the current one.
  aws s3api list-object-versions --bucket "$S3_BUCKET_NAME" \
    --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' --output json 2>/dev/null \
    | "$PYTHON_BIN" -c "
import json, sys
data = json.load(sys.stdin)
objects = data.get('Objects') or []
print(json.dumps(objects))
" > /tmp/chronolab_versions.json 2>/dev/null || echo '[]' > /tmp/chronolab_versions.json
  if [ -s /tmp/chronolab_versions.json ] && [ "$(cat /tmp/chronolab_versions.json)" != "[]" ] && [ "$(cat /tmp/chronolab_versions.json)" != "null" ]; then
    aws s3api delete-objects --bucket "$S3_BUCKET_NAME" \
      --delete "{\"Objects\": $(cat /tmp/chronolab_versions.json)}" >/dev/null 2>&1 || true
  fi
  rm -f /tmp/chronolab_versions.json
  aws s3api delete-bucket --bucket "$S3_BUCKET_NAME" >/dev/null 2>&1 || true
fi

# ── Amplify ──────────────────────────────────────────────────────────────
if [ -n "${AMPLIFY_APP_ID:-}" ]; then
  echo "Deleting Amplify app $AMPLIFY_APP_ID..."
  aws amplify delete-app --app-id "$AMPLIFY_APP_ID" >/dev/null 2>&1 || true
fi

echo ""
echo "== Teardown complete =="
echo "Note: .env still has the old generated values in it — delete .env (or just"
echo "the generated block at the bottom) before running bootstrap.sh again."
