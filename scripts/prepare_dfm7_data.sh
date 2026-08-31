#!/usr/bin/env bash
set -euo pipefail

# Prepare DFM7 with the Gemma 4 native chat template throughout.
# Run from the HRM-Text repo root:
#   bash scripts/prepare_dfm7_data.sh

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TOKENIZER_PATH="${TOKENIZER_PATH:-../brainsurgery/models/gemma4_31b/tokenizer.json}"
CHAT_TEMPLATE="${CHAT_TEMPLATE:-data_io/chat_templates/gemma4_native_chat.jinja}"
TOKENIZER_WORKERS="${TOKENIZER_WORKERS:-1}"
BASE_TOKENIZED="${BASE_TOKENIZED:-data/tokenized_dfm6}"
DFM7_SAMPLE_OUTPUT="${DFM7_SAMPLE_OUTPUT:-data/sampled_dfm7}"
DFM7_ANALYTICS_OUTPUT="${DFM7_ANALYTICS_OUTPUT:-data/show_analytics_dfm7.md}"

if [[ ! -f "$CHAT_TEMPLATE" ]]; then
  echo "Missing Gemma 4 chat template: $CHAT_TEMPLATE" >&2
  exit 1
fi

if [[ "$CHAT_TEMPLATE" != *"gemma4_native_chat.jinja" ]]; then
  echo "DFM7 must use the Gemma 4 native chat template, got: $CHAT_TEMPLATE" >&2
  exit 1
fi

if [[ "$TOKENIZER_PATH" != *"gemma4"* && "$TOKENIZER_PATH" != *"Gemma"* ]]; then
  echo "DFM7 must use the Gemma 4 tokenizer, got: $TOKENIZER_PATH" >&2
  exit 1
fi

python scripts/prepare_dfm7_special_sources.py --force
python scripts/shard_dfm7_large_parquets.py --force
python scripts/build_dfm7_chat_source_tree.py --force --new-only

python scripts/tokenize_chat_template.py \
  data/dfm7_chat_sources \
  --tokenizer-path "$TOKENIZER_PATH" \
  --chat-template "$CHAT_TEMPLATE" \
  --output-dir data/tokenized_dfm7_jinja \
  --workers "$TOKENIZER_WORKERS" \
  --skip-bad-json

python scripts/build_tokenized_dfm7_tree.py --force --base-tokenized "$BASE_TOKENIZED"

(
  cd data_io
  python sample_tokenized.py \
    tokenized_path=../data/tokenized_dfm7 \
    output_path="../${DFM7_SAMPLE_OUTPUT}" \
    epochs="${DFM7_EPOCHS:-5}" \
    concat_workers="${DFM7_CONCAT_WORKERS:-4}" \
    prefix_config_path=prefix_config_dfm7.yaml \
    > "../${DFM7_ANALYTICS_OUTPUT}"
)
