# Historical Available-Metric Averages Handoff

## Latest Available-Policy Clarification

The final implementation applies available-input averaging to the
`headline_avg_talemaader_v2` and `suite_avg_talemaader_v2` prefixes too. Missing
raw Talemaader v2 omits that task, not all other tasks. It never substitutes the
old scorer. The earlier omission of those entire XXL prefixes below is
superseded. Additional delta: `xxl-talemaader-delta-v4.json` under the output
directory, containing only those prefixes for nineteen checkpoints.
The original six-series publication remains unchanged.
The delta is now **synced and remotely verified** at all nineteen checkpoints:
`xxl-talemaader-delta-v4.synced.json` and
`xxl-talemaader-delta-v4.remote-verified.json`. Nine score series in total are
verified. No further XXL write is pending for the discovered historical points.

Final prepared snapshots: `xl-v4.json` (68 points, including current partial
3200K inputs) and `xxl-v4.json` (19). Source raw snapshots are linked and hashed;
no extra fetch or invented metric was used for this policy recomputation.
Use fresh post3200 preparation for XL publication, not the partial snapshot.
Twelve focused tests pass. Runtime source is frozen for scheduler integration.
Use the module invocation (`python -m scripts.backfill_available_eval_averages`),
not direct script-path invocation. For fresh3200 preparation, keep the final
definition-matched3200 summary; do not overwrite it with an older definition's
pre-backfill summary. Both points were sent to the scheduler owner for the
separate `schedule_historical_available_sync.py` integration.

## Scheduler Ownership

No XL history writes have been performed by this worker. Scheduler owner should
insert one CPU REPORT after **all 3200K raw sync and average jobs**, before 3250K
training. Do not stop the active GPU evaluations. Prepare at REPORT execution
time, so completed 3200K raw inputs are included and the last append does not
regress the summary to 3150K. Never reuse `xl-v1.json`: its implementation pins
are superseded.

Commands, from `/work/mimir/HRM-Text`, using hrm Python:

```bash
python -m scripts.backfill_available_eval_averages prepare --run xl --output logs/historical_available_averages_20261007/xl-after3200.json
python -m scripts.backfill_available_eval_averages sync --payload logs/historical_available_averages_20261007/xl-after3200.json --permit logs/historical_available_averages_20261007/xl-after3200-permit.json
```

The scheduler-owned permit JSON must contain `run_path`, the prepared
`payload_sha256`, and `exclusive_writer_confirmed: true`. Before granting it,
verify the prepared final point is step 3200000 and no conflicting epoch was
omitted. A run-specific flock serializes this tool; it does **not** magically
lock legacy scheduler writers. Dependency ordering is therefore mandatory.
The start receipt blocks ambiguous automatic retries after interrupted writes.
Successful repeat invocations with the same completed receipt are no-ops.

## Completed XXL-Wide Write

Run: `peter-sk-sdu/DFM5/dfm10-xxl-wide`.
Read-only local and original-host process checks found no trainer, scheduler,
or average writer for this run. Nineteen checkpoints were appended successfully.
The six new score series were independently fetched from W&B and all nineteen
checkpoint/epoch/value tuples matched the payload.

- Payload: `logs/historical_available_averages_20261007/xxl-v1.json`
- Permit: `xxl-permit.json` in that directory.
- Sync receipt: `xxl-v1.synced.json`.
- Remote proof: `xxl-v1.remote-verified.json`.
- Local SDK log: `wandb/run-20261007_034109-dfm10-xxl-wide/logs`.

Subsequent all-suite axis discovery in `xxl-v2.json` still found nineteen
checkpoints, so no duplicate/delta write is necessary. This later preparation
is evidence, not a second publication. Epoch 2's historical step-zero axis is
bound to actual checkpoint 754208, as documented in the DFM13 local-build wiki;
the epoch-1 evaluated checkpoint remains 353465, not the unevaluated 356640.

## Coverage And Missing Inputs

Initial XL preparation has 67 checkpoints. Danish, English, traditional overall,
DFM suite, and all-language v1/v2 have available-input scores at all 67. The
multilingual v1/v2 scores have inputs at seven checkpoints; the new13-language
score has inputs at one. Talemaader-only scores use actual v2 raw metrics at all
67, never old-scorer aliases.

XXL-wide has the six aforementioned available-input scores at all nineteen.
There are no inputs for its non-DA/EN multilingual/new13 scores and no raw
Talemaader-v2 scorer, so those scores are omitted, with coverage reported.
The all-language score at those points is based on available Danish/English
tasks, not an assertion of 34-language evaluation completeness.

All payloads preserve checkpoint-aligned raw values, selected history events,
excluded axis conflicts, definitions, hashes, and observed/expected coverage.
All-suite checkpoint discovery replaces the initial Talemaader-only discovery.
Returned raw-history event counts are checked against advertised W&B counts.
Discrepancies trigger exhaustive sparse scans and remain explicit in receipts:
XL Ukrainian Winogrande advertised seven events but both sampled and exhaustive
history returned six. No seventh value is invented.

## Implementation

- `scripts/backfill_available_eval_averages.py`
- `tests/test_backfill_available_eval_averages.py` (12 focused tests)
- Existing Harvey expanded-average and Boole population computation APIs are
  reused without modifying their definitions or files.
- No raw eval metrics, old average namespaces, GPU processes, or training state
  are modified by preparation or sync.
