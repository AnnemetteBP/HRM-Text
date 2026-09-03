import json
from pathlib import Path

from scripts.plot_moe_training import load_metrics, render


def test_moe_metrics_render_to_svg(tmp_path: Path) -> None:
    path = tmp_path / "metrics.jsonl"
    records = [
        {
            "event": "metrics",
            "step": step,
            "train/loss": 11.0 - step,
            "train/objective": 11.1 - step,
            "train/moe/balance_loss": 1.2,
            "train/moe/z_loss": 0.8,
            "train/moe/aux_loss": 0.0128,
            **{
                f"train/moe/expert_{expert}/load": 0.25
                for expert in range(4)
            },
            **{
                f"train/moe/expert_{expert}/mean_probability": 0.25
                for expert in range(4)
            },
        }
        for step in (1, 2)
    ]
    path.write_text("".join(json.dumps(record) + "\n" for record in records))

    svg = render(load_metrics(path), "test-run")

    assert svg.startswith("<svg")
    assert "Language-model training" in svg
    assert "expert_3/load" in svg
    assert "test-run" in svg
