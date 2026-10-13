# Andersen Modernization Validation

The original 119-example, zero-shot evaluation split. This is evaluation data,
not a training source. Training uses the separate 1,068-example split.

- Upstream corpus: https://github.com/ogierMontanus/hcandersenDk_data_2024
- License: AGPL-3.0; see LICENSE. Preserve upstream work-level scholarly credits.
- Alignment and split: original DFM10 paragraph-aligned modernization preparation.
- Retrieved 2026-10-11 from `/work/dfm/andersen/pairs_chunked_val.jsonl` on the
  original training machine, byte-identical to the DFM10 preparation checksum.
- SHA256: `7d635eb87ecab1fd88be0e290fe029d4af183fbafc0097f516fce0e7c60e91bf`
- Size: 471,923 bytes.

The HF training package `schneiderkamplab/dfm10-andersen-modernization` originally
published only train rows. This small versioned holdout fixes the portability gap
without exposing it to training-directory discovery. Run the eval scheduler from
the HRM-Text repository root, as for the other relative suite configuration paths.
