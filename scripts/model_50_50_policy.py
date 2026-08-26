import numpy as np
from pathlib import Path
import yaml

tree = Path("/work/dfm/HRM-Text/data/tokenized_dfm9")
cfg_path = Path("/work/dfm/HRM-Text-long-context/data_io/prefix_config_dfm9.yaml")
config_entries = yaml.safe_load(cfg_path.read_text())

def match_prefix(name):
    for e in config_entries:
        if name.startswith(e["prefix"]):
            return e
    return None

tasks = []
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
    rep = pcfg.get("repeat", 1)
    rts = (min(cap, n) if cap is not None else n) * rep
    sr = int((lens < 4096).sum()); st = float(lens[lens < 4096].sum())
    lr = int(((lens >= 4096) & (lens < 8192)).sum()); lt = float(lens[(lens >= 4096) & (lens < 8192)].sum())
    tasks.append((entry.name, rts, sr, st, lr, lt))

# Policy: long bin takes min(rts, lr) rows (no repetition, once per epoch).
# Short bin takes f * rts rows (capped at sr); solve f so short_tokens == long_tokens.
long_rows = sum(min(rts, lr) for _, rts, _, _, lr, _ in tasks)
long_tok = 0.0
for _, rts, sr, st, lr, lt in tasks:
    take = min(rts, lr)
    long_tok += take * (lt / lr if lr else 0)

# short token contribution as a function of f (per task, short pool is huge, no cap concern mostly)
num = 0.0
for _, rts, sr, st, lr, lt in tasks:
    if sr == 0:
        continue
    num += rts * (st / sr)   # full-quota short tokens
f = long_tok / num
short_rows = sum(min(f * rts, sr) for _, rts, sr, _, _, _ in tasks)
short_tok = sum(min(f * rts, sr) * (st / sr) for _, rts, sr, st, _, _ in tasks)
tot = long_tok + short_tok
print(f"long (no repetition, under caps): {long_rows:,} rows = {long_tok/1e9:.2f}B tok")
print(f"short fraction: {f:.4f} -> {short_rows:,.0f} rows = {short_tok/1e9:.2f}B tok")
print(f"TOTAL: {(long_rows+short_rows):,.0f} rows = {tot/1e9:.2f}B tokens/epoch")
print(f"tokens: long {100*long_tok/tot:.1f}% short {100*short_tok/tot:.1f}%")
print(f"rows:   long {100*long_rows/(long_rows+short_rows):.1f}% short {100*short_rows/(long_rows+short_rows):.1f}%")

# check short cap violations (tasks where f*rts > sr)
viol = [(name, int(f*rts), sr) for name, rts, sr, _, _, _ in tasks if f * rts > sr]
print(f"\ntasks where short target exceeds short pool: {len(viol)} of {len(tasks)}")
for v in viol[:5]:
    print("  ", v)
