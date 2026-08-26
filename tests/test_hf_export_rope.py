import json
from types import SimpleNamespace

import pytest
import yaml

from conversion.convert_to_hf import _build_rope_parameters
from eval_scheduler.runtime import validate_export_rope_config


def test_yarn_parameters_use_transformers_field_names():
    assert _build_rope_parameters(
        {
            "max_seq_len": 8192,
            "H_rope_scaling_type": "yarn",
            "H_rope_scaling_factor": 2.0,
        },
        10000.0,
    ) == {
        "rope_type": "yarn",
        "factor": 2.0,
        "original_max_position_embeddings": 4096,
        "rope_theta": 10000.0,
    }


def test_export_validation_rejects_default_rope_for_yarn_checkpoint(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    export = tmp_path / "export"
    checkpoint.mkdir()
    export.mkdir()
    (checkpoint / "all_config.yaml").write_text(
        yaml.safe_dump(
            {
                "arch": {
                    "H_rope_scaling_type": "yarn",
                    "H_rope_scaling_factor": 2.0,
                }
            }
        )
    )
    (export / "config.json").write_text(
        json.dumps({"rope_parameters": {"rope_type": "default", "rope_theta": 10000.0}})
    )
    job = SimpleNamespace(metadata={"ckpt_path": str(checkpoint)})

    with pytest.raises(ValueError, match="RoPE type mismatch"):
        validate_export_rope_config(job, export)
