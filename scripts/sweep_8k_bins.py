import numpy as np
from pathlib import Path
import yaml

tree = Path("/work/dfm/HRM-Text/data/tokenized_dfm9")
cfg_path = Path("/work/dfm/HRM-Text-long-context/data_io/prefix_config_dfm9.yaml")
bins = [(0, 4096), (4096, 8192)]
config_entries = yaml.safe_load(cfg_path.read_text())

def match_prefix(name):
    for e in config_entries:
        if name.startswith(e["prefix"]):
            return e
    return None

# Precompute per-task pool stats once
task_pools = []  # (rows_to_sample, short_rows, short_tok, long_rows, long_tok)
for entry in sorted(tree.iterdir()):
    if not entry.is_dir():
        continue
    pcfg = match_prefix(entry.name)
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
    m_short = lens < 4096
    m_long = (lens >= 4096) & (lens < 8192)
    task_pools.append((
        rows_to_sample,
        int(m_short.sum()), float(lens[m_short].sum()),
        int(m_long.sum()), float(lens[m_long].sum()),
    ))

print(f"tasks: {len(task_pools)}")
for f_short in (0.5, 0.4, 0.3, 0.25, 0.2):
    f_long = 1.0 - f_short
    short_r = long_r = 0.0
    short_t = long_t = 0.0
    for rows_to_sample, sr, st, lr, lt in task_pools:
        st_r = int(round(rows_to_sample * f_short))
        lt_r = int(round(rows_to_sample * f_long))
        if sr > 0 and st_r > 0:
            short_r += st_r
            short_t += st_r * (st / sr if sr else 0)
        if lr > 0 and lt_r > 0:
            long_r += lt_r
            long_t += lt_r * (lt / lr if lr else 0)
    tot_r = short_r + long_r
    tot_t = short_t + long_t
    print(f"  short frac={f_short:.2f}: 4K-8K rows {100*long_r/tot_r:5.1f}% | 4K-8K tokens {100*long_t/tot_t:5.1f}% | rows {tot_r:,.0f} | tok {tot_t:,.0f}")
