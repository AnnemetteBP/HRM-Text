from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.launch_multinode_torchrun import parse_hostfile, remote_agent_command


def test_parse_hostfile_preserves_order_and_comments(tmp_path: Path) -> None:
    hostfile = tmp_path / "hosts"
    hostfile.write_text("node-b # rank zero\n\nnode-a\n")
    assert parse_hostfile(hostfile) == ["node-b", "node-a"]


def test_parse_hostfile_rejects_duplicates(tmp_path: Path) -> None:
    hostfile = tmp_path / "hosts"
    hostfile.write_text("node-a\nnode-a\n")
    with pytest.raises(ValueError, match="duplicate"):
        parse_hostfile(hostfile)


def test_remote_agent_command_contains_fixed_membership_and_exact_pid() -> None:
    args = SimpleNamespace(
        python_env="/env with spaces",
        workdir="/repo with spaces",
        nproc_per_node=8,
        env=["OMP_NUM_THREADS=1"],
        nccl_interface="ib0",
    )
    command = remote_agent_command(
        args=args,
        host_count=4,
        node_rank=2,
        master_addr="10.0.0.1",
        master_port=29500,
        command=["pretrain.py", "data=dfm8"],
        pid_path=Path("/shared/run/node_02.pid"),
    )
    assert "--nnodes=4" in command
    assert "--nproc-per-node=8" in command
    assert "--node-rank=2" in command
    assert "--master-addr=10.0.0.1" in command
    assert "NCCL_SOCKET_IFNAME=ib0" in command
    assert "echo $$" in command
    assert "pretrain.py data=dfm8" in command
