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

echo "== ChronoLab bootstrap =="
echo "AWS_MODE=${AWS_MODE:-<unset>}"

if [ "${AWS_MODE:-local}" = "cloud" ]; then
  require_var AWS_REGION
  require_var BEDROCK_REGION
  require_var RESOURCE_SUFFIX

  if ! command -v aws >/dev/null 2>&1; then
    echo "ERROR: AWS CLI not found on PATH." >&2
    exit 1
  fi

  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "ERROR: 'aws sts get-caller-identity' failed. Run 'aws configure' first." >&2
    exit 1
  fi

  echo "Preflight OK — AWS CLI present, credentials valid."
  # Step 1 (budget alarm), Bedrock access check, and per-phase provisioning
  # are appended here by later phases of the migration plan.
else
  echo "AWS_MODE=local — targeting LocalStack at ${LOCALSTACK_ENDPOINT_URL:-http://localhost:4566}."
  echo "No cloud resources will be created. Provisioning against LocalStack happens in-app via backend/config.py."
fi

echo "== bootstrap.sh stub complete =="
