import numpy as np
from pathlib import Path
import yaml

tree = Path("/work/dfm/HRM-Text/data/tokenized_dfm9")
cfg_path = Path("/work/dfm/HRM-Text-long-context/data_io/prefix_config_dfm9.yaml")
bins = [(0, 4096), (4096, 8192)]
N_BINS = len(bins)

config_entries = yaml.safe_load(cfg_path.read_text())

def match_prefix(name):
    for e in config_entries:
        if name.startswith(e["prefix"]):
            return e
    return None

# Per-task (directory) simulation, faithful to sample_tokenized.py
rows_out = {b: 0 for b in bins}
tok_out = {b: 0 for b in bins}
bin_pool = {b: 0 for b in bins}
long_pool_repeat_sum = 0  # number of long rows actually emitted / long rows in pool
n_tasks_with_long = 0
skipped_long_tasks = 0

for entry in sorted(tree.iterdir()):
    if not entry.is_dir():
        continue
    name = entry.name
    pcfg = match_prefix(name)
    if pcfg is None:
        continue
    il, rl = entry / "inst_len.npy", entry / "resp_len.npy"
    if not (il.exists() and rl.exists()):
        continue
    lens = np.load(il, mmap_mode="r") + np.load(rl, mmap_mode="r")
    n = len(lens)
    if n == 0:
        continue
    cap = pcfg.get("max_per_file")
    rows_to_sample = (min(cap, n) if cap is not None else n) * pcfg.get("repeat", 1)
    counts = {}
    toks = {}
    for b in bins:
        m = (lens >= b[0]) & (lens < b[1])
        counts[b] = int(m.sum())
        toks[b] = float(lens[m].sum())
        bin_pool[b] += counts[b]
    for b in bins:
        target = int(round(rows_to_sample * 0.5))
        if counts[b] == 0 or target == 0:
            if b == (4096, 8192):
                skipped_long_tasks += 1
            continue
        avg = toks[b] / counts[b]
        rows_out[b] += target
        tok_out[b] += target * avg
        if b == (4096, 8192):
            long_pool_repeat_sum += target
            n_tasks_with_long += 1

tot_r = rows_out[bins[0]] + rows_out[bins[1]]
tot_t = tok_out[bins[0]] + tok_out[bins[1]]
print("PER-TASK SIMULATION (matches sampler logic, current 4K-era tree):")
print(f"  <=4K rows:  {rows_out[bins[0]]:>14,} ({100*rows_out[bins[0]]/tot_r:5.1f}%)   tokens {tok_out[bins[0]]:>16,.0f} ({100*tok_out[bins[0]]/tot_t:5.1f}%)")
print(f"  4K-8K rows: {rows_out[bins[1]]:>14,} ({100*rows_out[bins[1]]/tot_r:5.1f}%)   tokens {tok_out[bins[1]]:>16,.0f} ({100*tok_out[bins[1]]/tot_t:5.1f}%)")
print(f"\n  global 4K-8K pool rows (all tasks): {bin_pool[bins[1]]:,}")
print(f"  tasks with >=1 4K-8K row: {n_tasks_with_long}   tasks whose long bin was skipped (empty): {skipped_long_tasks}")
if n_tasks_with_long:
    print(f"  avg repetition of 4K-8K rows (emitted/pool): {long_pool_repeat_sum/bin_pool[bins[1]]:.1f}x")
