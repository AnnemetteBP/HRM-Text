#!/usr/bin/env bash
set -euo pipefail

# Prepare the focused DFM8-post sample. Run only after the full DFM8 tokenized
# tree has been rebuilt with the final DFM8 additions.
#
# Run from the HRM-Text repo root:
#   bash scripts/prepare_dfm8_post_data.sh

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DFM8_TOKENIZED_ROOT="${DFM8_TOKENIZED_ROOT:-data/tokenized_dfm8}"
DFM8_POST_TOKENIZED_ROOT="${DFM8_POST_TOKENIZED_ROOT:-data/tokenized_dfm8_post}"
DFM8_POST_SAMPLE_OUTPUT="${DFM8_POST_SAMPLE_OUTPUT:-data/sampled_dfm8_post}"
DFM8_POST_ANALYTICS_OUTPUT="${DFM8_POST_ANALYTICS_OUTPUT:-data/show_analytics_dfm8_post.md}"
DFM8_POST_EPOCHS="${DFM8_POST_EPOCHS:-1}"
DFM8_POST_CONCAT_WORKERS="${DFM8_POST_CONCAT_WORKERS:-4}"
DFM8_POST_REUSE_TOKENS="${DFM8_POST_REUSE_TOKENS:-false}"

if [[ ! -f "$DFM8_TOKENIZED_ROOT/tokenizer_info.json" ]]; then
  echo "Missing $DFM8_TOKENIZED_ROOT/tokenizer_info.json; build full DFM8 tokenized data first." >&2
  exit 1
fi

python scripts/build_tokenized_dfm8_post_tree.py \
  --root "$DFM8_TOKENIZED_ROOT" \
  --output "$DFM8_POST_TOKENIZED_ROOT" \
  --force

(
  cd data_io
  python sample_tokenized.py \
    tokenized_path="../${DFM8_POST_TOKENIZED_ROOT}" \
    output_path="../${DFM8_POST_SAMPLE_OUTPUT}" \
    epochs="$DFM8_POST_EPOCHS" \
    concat_workers="$DFM8_POST_CONCAT_WORKERS" \
    prefix_config_path=prefix_config_dfm8_post.yaml \
    reuse_tokens="$DFM8_POST_REUSE_TOKENS" \
    > "../${DFM8_POST_ANALYTICS_OUTPUT}"
)

echo "Wrote ${DFM8_POST_SAMPLE_OUTPUT}"
echo "Wrote ${DFM8_POST_ANALYTICS_OUTPUT}"
echo "Review the analytics and tune data_io/prefix_config_dfm8_post.yaml if broad anchors are not close to 20%."
