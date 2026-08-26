import numpy as np
from pathlib import Path

tree = Path("/work/dfm/HRM-Text/data/tokenized_dfm9")
bins = [(0, 4096), (4096, 8192), (8192, 16384), (16384, 32768)]
totals = {b: 0 for b in bins}
tokens_per_bin = {b: 0 for b in bins}
rows_per_source = {}
total_rows = 0
total_tokens = 0

for entry in sorted(tree.iterdir()):
    if not entry.is_dir():
        continue
    il = entry / "inst_len.npy"
    rl = entry / "resp_len.npy"
    if not (il.exists() and rl.exists()):
        continue
    inst_len = np.load(il, mmap_mode="r")
    resp_len = np.load(rl, mmap_mode="r")
    lens = inst_len + resp_len
    n = len(lens)
    tok = int(lens.sum())
    total_rows += n
    total_tokens += tok
    src = entry.name.split("__")[0]
    rows_per_source[src] = rows_per_source.get(src, 0) + n
    for b in bins:
        m = (lens >= b[0]) & (lens < b[1])
        c = int(m.sum())
        totals[b] += c
        tokens_per_bin[b] += int(lens[m].sum())

print(f"total rows: {total_rows:,}  total tokens: {total_tokens:,}")
print()
print("BY ROWS:")
for b in bins:
    c = totals[b]
    print(f"  {b[0]:>6}-{b[1]:>6}: {c:>12,} rows  ({100*c/total_rows:.1f}%)")
print("BY TOKENS:")
for b in bins:
    c = tokens_per_bin[b]
    print(f"  {b[0]:>6}-{b[1]:>6}: {c:>15,} tok  ({100*c/total_tokens:.1f}%)")
print()
print("top sources by row count:")
for src, c in sorted(rows_per_source.items(), key=lambda x: -x[1])[:25]:
    print(f"  {src:60s} {c:>12,}")
