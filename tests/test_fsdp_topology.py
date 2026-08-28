from unittest.mock import MagicMock
import json
from types import SimpleNamespace

import pytest

import pretrain


def config(*, shard_degree=None, reshard=None):
    return pretrain.PretrainConfig.model_construct(
        fsdp_shard_degree=shard_degree,
        fsdp_reshard_after_forward=reshard,
    )


def test_reshard_default_preserves_checkpointing_behavior() -> None:
    cfg = config()
    assert pretrain.fsdp_reshard_after_forward(cfg, checkpointed=False) is False
    assert pretrain.fsdp_reshard_after_forward(cfg, checkpointed=True) is True


@pytest.mark.parametrize("value", [False, True])
def test_explicit_reshard_overrides_checkpointing(value: bool) -> None:
    cfg = config(reshard=value)
    assert pretrain.fsdp_reshard_after_forward(cfg, checkpointed=False) is value
    assert pretrain.fsdp_reshard_after_forward(cfg, checkpointed=True) is value


def test_hsdp_mesh_uses_replicate_then_shard(monkeypatch) -> None:
    mesh = MagicMock()
    init_mesh = MagicMock(return_value=mesh)
    monkeypatch.setattr(pretrain.dist, "is_available", lambda: True)
    monkeypatch.setattr(pretrain.dist, "is_initialized", lambda: True)
    monkeypatch.setattr(pretrain.dist, "get_world_size", lambda: 8)
    monkeypatch.setattr(pretrain, "init_device_mesh", init_mesh)
    monkeypatch.setenv("LOCAL_WORLD_SIZE", "8")

    assert pretrain.create_fsdp_mesh(config(shard_degree=4)) is mesh
    init_mesh.assert_called_once_with(
        "cuda", (2, 4), mesh_dim_names=("replicate", "shard")
    )


def test_full_world_degree_preserves_default_mesh(monkeypatch) -> None:
    monkeypatch.setattr(pretrain.dist, "is_available", lambda: True)
    monkeypatch.setattr(pretrain.dist, "is_initialized", lambda: True)
    monkeypatch.setattr(pretrain.dist, "get_world_size", lambda: 8)
    monkeypatch.setenv("LOCAL_WORLD_SIZE", "8")
    assert pretrain.create_fsdp_mesh(config(shard_degree=8)) is None


@pytest.mark.parametrize("degree", [3, 16])
def test_invalid_shard_degree_is_rejected(monkeypatch, degree: int) -> None:
    monkeypatch.setattr(pretrain.dist, "is_available", lambda: True)
    monkeypatch.setattr(pretrain.dist, "is_initialized", lambda: True)
    monkeypatch.setattr(pretrain.dist, "get_world_size", lambda: 8)
    monkeypatch.setenv("LOCAL_WORLD_SIZE", "8")
    with pytest.raises(ValueError):
        pretrain.create_fsdp_mesh(config(shard_degree=degree))


def test_world_size_change_uses_global_row_cursor(monkeypatch, tmp_path) -> None:
    tag = "step_10"
    (tmp_path / f"checkpoint_state_{tag}.json").write_text(json.dumps({
        "step": 10,
        "epoch": 1,
        "batch_in_epoch": 40,
        "batch_in_epoch_exact": True,
        "global_row_cursor_in_epoch": 1234,
        "local_batch_size": 8192,
        "world_size": 8,
    }))
    cfg = pretrain.PretrainConfig.model_construct(
        resume_checkpoint_path=str(tmp_path),
        resume_checkpoint_tag=tag,
        resume_epoch=None,
        resume_step=None,
        resume_batch_in_epoch=None,
    )
    monkeypatch.setattr(pretrain.dist, "is_available", lambda: True)
    monkeypatch.setattr(pretrain.dist, "is_initialized", lambda: True)
    monkeypatch.setattr(pretrain.dist, "get_world_size", lambda: 4)

    state = pretrain.resolve_resume_state(cfg, current_local_batch_size=8192)
    assert state is not None
    assert state.resume_mode == "row_cursor"
    assert state.start_row_cursor == 1234


def test_no_carry_checkpoint_writes_atomic_sidecar_without_carry(monkeypatch, tmp_path) -> None:
    cfg = pretrain.PretrainConfig.model_construct(
        checkpoint_path=str(tmp_path),
        checkpoint_format="sharded",
        gradient_accumulation_steps=4,
        global_batch_size=262144,
        data=SimpleNamespace(path="data/test"),
        seed=0,
        fsdp_shard_degree=4,
        fsdp_reshard_after_forward=None,
    )
    state = SimpleNamespace(step=10, carry=None)
    save_state = MagicMock()
    monkeypatch.setattr(pretrain, "save_sharded_train_state", save_state)

    pretrain.save_train_checkpoint(
        cfg, state, "step_10", epoch=1, batch_in_epoch=40, rank=0,
        local_batch_size=8192,
    )

    save_state.assert_called_once()
    metadata = json.loads((tmp_path / "checkpoint_state_step_10.json").read_text())
    assert metadata["carry_policy"] == "none"
    assert metadata["world_size"] == 1
    assert metadata["fsdp_shard_degree"] == 4
    assert not list(tmp_path.glob("carry_step_10.*.pt"))
    assert not (tmp_path / "checkpoint_state_step_10.json.tmp").exists()
