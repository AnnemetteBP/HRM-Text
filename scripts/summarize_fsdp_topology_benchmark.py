#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


def peak_memory(log_path: Path) -> float | None:
    values = [
        float(value)
        for value in re.findall(r"max_allocated=([0-9.]+) MiB", log_path.read_text(errors="replace"))
    ]
    return max(values) if values else None


def relative_error(left: float, right: float) -> float:
    return abs(left - right) / max(abs(left), abs(right), 1e-30)


def main() -> None:
    root = Path(sys.argv[1])
    rows = []
    results = {}
    for path in sorted(root.glob("*/bench.json")):
        result = json.loads(path.read_text())
        results[path.parent.name] = result
        rows.append({
            "case": path.parent.name,
            "world": result["world_size"],
            "gas": result["gradient_accumulation_steps"],
            "median_s": result["median_step_seconds"],
            "peak_mib": peak_memory(path.parent / "train.log"),
            "loss": result.get("last_metrics", {}).get("train/loss"),
        })

    reference = results.get("degree8_auto", {}).get("state_fingerprint", {})
    comparisons = {}
    for name, result in results.items():
        fingerprint = result.get("state_fingerprint", {})
        comparisons[name] = {
            key: {
                field: relative_error(reference[key][field], values[field])
                for field in ("sum", "abs_sum", "square_sum", "abs_max")
            }
            for key, values in fingerprint.items()
            if key in reference
        }

    output = {"runs": rows, "fingerprint_relative_error_vs_degree8_auto": comparisons}
    (root / "summary.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
