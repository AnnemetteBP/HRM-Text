from torch import nn
from torch.distributed._composable import checkpoint

from models.transformer import TransformerBlock


def apply_full_activation_checkpointing(model: nn.Module) -> int:
    """Checkpoint every TransformerBlock without changing module FQNs."""
    blocks = [module for module in model.modules() if isinstance(module, TransformerBlock)]
    for block in blocks:
        checkpoint(block)
    return len(blocks)
