#!/usr/bin/env bash
set -euo pipefail

log_root="${1:-logs/training}"
poll_seconds="${2:-10}"
current_log=""
tail_pid=""

cleanup() {
    if [[ -n "${tail_pid}" ]] && kill -0 "${tail_pid}" 2>/dev/null; then
        kill "${tail_pid}" 2>/dev/null || true
        wait "${tail_pid}" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

while true; do
    latest_entry="$(
        find "${log_root}" -type f -name 'train_until_step_*.log' \
            -printf '%T@ %p\n' 2>/dev/null \
            | sort -nr \
            | head -n 1
    )"
    latest_log="${latest_entry#* }"

    if [[ -n "${latest_entry}" && "${latest_log}" != "${current_log}" ]]; then
        cleanup
        current_log="${latest_log}"
        printf '\nFollowing newest training log: %s\n\n' "${current_log}"
        tail -n 120 -F "${current_log}" &
        tail_pid=$!
    fi

    sleep "${poll_seconds}"
done
