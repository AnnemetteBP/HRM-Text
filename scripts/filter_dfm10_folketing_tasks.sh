#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

AUDIT_ROOT="${AUDIT_ROOT:-logs/dfm10_folketing_audit}"
AUDIT_FILE="${AUDIT_FILE:-$AUDIT_ROOT/export_judge.audit.jsonl}"
OUTPUT_ROOT="${OUTPUT_ROOT:-data/dfm10_folketing_transform_sources_audited}"

if [[ ! -s "$AUDIT_FILE" ]]; then
  echo "Missing audit file: $AUDIT_FILE" >&2
  exit 2
fi

python scripts/audit_export_datasets.py filter \
  --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-denoising \
  --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-error-correction \
  --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-prefix-continuation \
  --dataset-root data/dfm10_folketing_transform_sources/folketingets-dokumenter-span-filling \
  --audit "$AUDIT_FILE" \
  --output-root "$OUTPUT_ROOT" \
  --force
