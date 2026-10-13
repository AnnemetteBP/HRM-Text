from unittest.mock import Mock, patch

import pytest

from training_suspend.nccl_shim import NcclCheckpointShim


def test_requires_rendezvous(monkeypatch):
    monkeypatch.delenv('NCCL_CHECKPOINT_KVS_PATH', raising=False)
    with pytest.raises(RuntimeError, match='KVS_PATH'):
        NcclCheckpointShim()


def test_requires_preload(monkeypatch):
    monkeypatch.setenv('NCCL_CHECKPOINT_KVS_PATH', '/unused')
    with patch('ctypes.CDLL', return_value=object()):
        with pytest.raises(RuntimeError, match='LD_PRELOAD'):
            NcclCheckpointShim()


def test_calls_and_propagates_failure(monkeypatch):
    monkeypatch.setenv('NCCL_CHECKPOINT_KVS_PATH', '/unused')
    library = Mock()
    library.ncclCheckpointPrepare.return_value = 0
    library.ncclCheckpointRestore.return_value = 0
    with patch('ctypes.CDLL', return_value=library):
        shim = NcclCheckpointShim()
    shim.prepare()
    shim.restore()
    library.ncclCheckpointPrepare.assert_called_once_with()
    library.ncclCheckpointRestore.assert_called_once_with()
    library.ncclCheckpointRestore.return_value = 5
    with pytest.raises(RuntimeError, match='status 5'):
        shim.restore()
