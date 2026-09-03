from pathlib import Path
from unittest.mock import Mock, patch

from conversion import convert_to_hf


def test_convert_passes_resolved_tokenizer_override_to_checkpoint_loader(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tokenizer_dir = tmp_path / "tokenizer"
    tokenizer_dir.mkdir()
    output_dir = tmp_path / "output"
    checkpoint = Mock()
    checkpoint.model.state_dict.return_value = {}
    metadata = Mock()
    metadata.tokenizer_info = {}
    model_config = Mock()
    model_config.arch.model_dump.return_value = {}
    tokenizer = Mock()

    monkeypatch.setattr(
        "sys.argv",
        [
            "convert_to_hf.py",
            "--ckpt_path",
            str(tmp_path / "checkpoint"),
            "--ckpt_tag",
            "step_250000",
            "--out_dir",
            str(output_dir),
            "--tokenizer_path",
            str(tokenizer_dir),
        ],
    )
    with (
        patch.object(convert_to_hf, "load_config", return_value=(metadata, model_config, {})),
        patch.object(convert_to_hf, "load_tokenizer", return_value=tokenizer),
        patch.object(convert_to_hf, "set_tokenizer_special_tokens", return_value=tokenizer),
        patch.object(convert_to_hf, "build_hf_config", return_value={}),
        patch.object(convert_to_hf, "inference_load_checkpoint", return_value=checkpoint) as load_checkpoint,
        patch.object(convert_to_hf, "convert_state_dict", return_value=({}, [])),
        patch.object(convert_to_hf, "validate_vllm_packed_state"),
        patch.object(convert_to_hf, "save_file"),
    ):
        convert_to_hf.main()

    load_checkpoint.assert_called_once_with(
        str(tmp_path / "checkpoint"),
        None,
        True,
        ckpt_tag="step_250000",
        tokenizer_path_override=tokenizer_dir,
    )
