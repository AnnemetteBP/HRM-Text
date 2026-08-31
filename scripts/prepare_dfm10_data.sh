#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TOKENIZER_PATH="${TOKENIZER_PATH:-../brainsurgery/models/gemma4_31b/tokenizer.json}"
CHAT_TEMPLATE="${CHAT_TEMPLATE:-data_io/chat_templates/gemma4_native_chat.jinja}"
TOKENIZER_WORKERS="${TOKENIZER_WORKERS:-16}"
FOLKETING_ARCHIVE="${FOLKETING_ARCHIVE:-data/downloads/datasets/folketingets_dokumenter_14004/14004.zip}"

if [[ ! -s "$FOLKETING_ARCHIVE" ]]; then
  echo "Downloading Rigsarkivet Folketinget handover 14004..."
  mkdir -p "$(dirname "$FOLKETING_ARCHIVE")"
  curl -L --fail --retry 5 --retry-delay 5 --continue-at - \
    https://digidata.rigsarkivet.dk/download/14004 \
    -o "$FOLKETING_ARCHIVE"
fi

echo "Validating Andersen train/validation partition..."
python scripts/prepare_dfm10_andersen.py --force

echo "Downloading approved Alexandra Institute DFM10 train sources..."
python scripts/download_training_datasets.py \
  --download \
  --groups dfm10 \
  --only alexandra_nordjylland_news,alexandra_scandi_qa,alexandra_multi_zebra_logic,alexandra_dane,alexandra_dacoref,zai_deepdive

echo "Converting approved Alexandra Institute DFM10 train sources..."
python scripts/prepare_dfm10_alexandra.py --force

echo "Converting Z.ai DeepDive trajectories to Gemma 4 native tool use..."
python scripts/prepare_dfm10_deepdive.py --force

echo "Generating Folketinget self-supervised transformation tasks..."
python scripts/prepare_dfm10_folketing_tasks.py --force

echo "Tokenizing Andersen training split with the Gemma 4 template..."
python scripts/tokenize_chat_template.py \
  data/dfm10_andersen_sources \
  --tokenizer-path "$TOKENIZER_PATH" \
  --chat-template "$CHAT_TEMPLATE" \
  --output-dir data/tokenized_dfm10_andersen \
  --workers "$TOKENIZER_WORKERS" \
  --force

echo "Tokenizing Alexandra Institute training splits with the Gemma 4 template..."
python scripts/tokenize_chat_template.py \
  data/dfm10_alexandra_sources \
  --tokenizer-path "$TOKENIZER_PATH" \
  --chat-template "$CHAT_TEMPLATE" \
  --output-dir data/tokenized_dfm10_alexandra \
  --workers "$TOKENIZER_WORKERS" \
  --force

echo "Tokenizing native Z.ai DeepDive search trajectories..."
python scripts/tokenize_chat_template.py \
  data/dfm10_deepdive_sources \
  --tokenizer-path "$TOKENIZER_PATH" \
  --chat-template "$CHAT_TEMPLATE" \
  --output-dir data/tokenized_dfm10_deepdive \
  --workers "$TOKENIZER_WORKERS" \
  --force

FOLKETING_AUDITED_ROOT="${FOLKETING_AUDITED_ROOT:-data/dfm10_folketing_transform_sources_audited}"
if [[ ! -d "$FOLKETING_AUDITED_ROOT" ]]; then
  echo "Folketinget candidates are ready for audit, but no filtered tree exists at $FOLKETING_AUDITED_ROOT."
  echo "Run scripts/audit_dfm10_folketing_tasks.sh and scripts/filter_dfm10_folketing_tasks.sh before tokenization."
  exit 2
fi

echo "Tokenizing audited Folketinget transformation tasks with the Gemma 4 template..."
python scripts/tokenize_chat_template.py \
  "$FOLKETING_AUDITED_ROOT" \
  --tokenizer-path "$TOKENIZER_PATH" \
  --chat-template "$CHAT_TEMPLATE" \
  --output-dir data/tokenized_dfm10_folketing \
  --workers "$TOKENIZER_WORKERS" \
  --force

echo "Building DFM10 tokenized union tree..."
python scripts/build_tokenized_dfm10_tree.py --folketing data/tokenized_dfm10_folketing --force

if [[ "${DFM10_SAMPLE:-0}" == "1" ]]; then
  echo "Sampling DFM10 (${DFM10_EPOCHS:-10} epochs)..."
  (
    cd data_io
    python sample_tokenized.py \
      tokenized_path=../data/tokenized_dfm10 \
      output_path=../data/sampled_dfm10 \
      epochs="${DFM10_EPOCHS:-10}" \
      concat_workers="${DFM10_CONCAT_WORKERS:-4}" \
      prefix_config_path=prefix_config_dfm10.yaml \
      > ../data/show_analytics_dfm10.md
  )
else
  echo "DFM10 tokenized tree is ready. Set DFM10_SAMPLE=1 to sample it."
fi
