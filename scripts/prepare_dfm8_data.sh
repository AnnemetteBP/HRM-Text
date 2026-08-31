#!/usr/bin/env bash
set -euo pipefail

# Prepare DFM8 with the Gemma 4 native chat template throughout.
# Run from the HRM-Text repo root:
#   bash scripts/prepare_dfm8_data.sh

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TOKENIZER_PATH="${TOKENIZER_PATH:-../brainsurgery/models/gemma4_31b/tokenizer.json}"
CHAT_TEMPLATE="${CHAT_TEMPLATE:-data_io/chat_templates/gemma4_native_chat.jinja}"
TOKENIZER_WORKERS="${TOKENIZER_WORKERS:-1}"
BASE_TOKENIZED="${BASE_TOKENIZED:-data/tokenized_dfm7}"
DFM8_SAMPLE_OUTPUT="${DFM8_SAMPLE_OUTPUT:-data/sampled_dfm8}"
DFM8_ANALYTICS_OUTPUT="${DFM8_ANALYTICS_OUTPUT:-data/show_analytics_dfm8.md}"

if [[ ! -f "$CHAT_TEMPLATE" ]]; then
  echo "Missing Gemma 4 chat template: $CHAT_TEMPLATE" >&2
  exit 1
fi

if [[ "$CHAT_TEMPLATE" != *"gemma4_native_chat.jinja" ]]; then
  echo "DFM8 must use the Gemma 4 native chat template, got: $CHAT_TEMPLATE" >&2
  exit 1
fi

if [[ "$TOKENIZER_PATH" != *"gemma4"* && "$TOKENIZER_PATH" != *"Gemma"* ]]; then
  echo "DFM8 must use the Gemma 4 tokenizer, got: $TOKENIZER_PATH" >&2
  exit 1
fi

python scripts/convert_dfm8_giannor_tv2r.py --force
python scripts/convert_dfm8_skolegpt.py --force
if [[ "${DFM8_REBUILD_TRANSFORM_EXPANSION:-0}" == "1" ]]; then
  python scripts/build_dfm8_transform_expansion.py --force --target-multiplier 2.5
fi
if [[ "${DFM8_FILTER_TRANSFORM_EXPANSION:-1}" == "1" ]]; then
  python scripts/filter_dfm8_transform_expansion_audits.py --force
fi
python scripts/build_dfm8_chat_source_tree.py --force --new-only
python scripts/audit_dfm8_sources.py

python scripts/tokenize_chat_template.py \
  data/dfm8_chat_sources \
  --tokenizer-path "$TOKENIZER_PATH" \
  --chat-template "$CHAT_TEMPLATE" \
  --output-dir data/tokenized_dfm8_jinja \
  --workers "$TOKENIZER_WORKERS" \
  --skip-bad-json

python scripts/build_tokenized_dfm8_tree.py --force --base-tokenized "$BASE_TOKENIZED"
python scripts/report_dfm8_mix.py

(
  cd data_io
  python sample_tokenized.py \
    tokenized_path=../data/tokenized_dfm8 \
    output_path="../${DFM8_SAMPLE_OUTPUT}" \
    epochs="${DFM8_EPOCHS:-5}" \
    concat_workers="${DFM8_CONCAT_WORKERS:-4}" \
    prefix_config_path=prefix_config_dfm8.yaml \
    > "../${DFM8_ANALYTICS_OUTPUT}"
)
