#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

: "${AUDIT_BASE_URL:?Set AUDIT_BASE_URL to an OpenAI-compatible /v1 endpoint}"
: "${AUDIT_MODEL:?Set AUDIT_MODEL to the served judge model}"

AUDIT_ROOT="${AUDIT_ROOT:-logs/dfm10_folketing_audit}"
CONCURRENCY="${CONCURRENCY:-32}"

python scripts/audit_export_datasets.py audit \
  --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-denoising \
  --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-error-correction \
  --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-prefix-continuation \
  --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-span-filling \
  --audit-root "$AUDIT_ROOT" \
  --base-url "$AUDIT_BASE_URL" \
  --model "$AUDIT_MODEL" \
  --concurrency "$CONCURRENCY" \
  --retries "${RETRIES:-3}" \
  --force
