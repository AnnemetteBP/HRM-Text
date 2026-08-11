---
type: Operational Record
title: Filesystem / Scratch State
description: 'Part of Current State: Filesystem / Scratch State.'
tags:
- operations
- training
- evaluation
- runtime
status: stable
last_updated: 2026-08-10
confidence: high
part_of: /pages/current-state.md
---
# Filesystem / Scratch State

Part of [Current State](/pages/current-state.md).

Verified on 2026-05-21:

- `/work` and `/work/dfm` are WEKA (`wekafs`) mounts.
- `/tmp`, `/var/tmp`, `/mnt`, `/opt`, and `/var/lib` resolve to the container root overlay, not to a separate clean local scratch mount.
- `/dev/shm` is tmpfs with about `2.8T` available; avoid using it for this pipeline unless explicitly chosen, because it consumes RAM-backed memory.
- `/etc/ucloud` and `/opt/ucloud` are local XFS empty-dir mounts but only about `46G`, too small for the tokenizer staging experiments.
- The node exposes NVMe block devices (`nvme0n1` and `nvme1n1`), but no large directly mounted writable NVMe scratch path is visible inside the container.

Operational consequence: the failed `/tmp/tokenize` staging attempt was not a good test of a clean local disk. Until a real local NVMe scratch mount is provided by UCloud/admin, run tokenization from `/work/dfm/HRM-Text` with a small worker count and `nice`/`ionice`.
