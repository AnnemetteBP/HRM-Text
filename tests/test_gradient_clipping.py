import pytest
import torch

from models.gradient_clipping import clip_grad_norm_mean_units


def parameter_with_grad(values: list[float]) -> torch.nn.Parameter:
    parameter = torch.nn.Parameter(torch.zeros(len(values)))
    parameter.grad = torch.tensor(values)
    return parameter


def test_high_threshold_preserves_gradient_exactly() -> None:
    parameter = parameter_with_grad([3.0, 4.0])
    original = parameter.grad.clone()

    metrics = clip_grad_norm_mean_units([parameter], max_norm=1e9)

    assert torch.equal(parameter.grad, original)
    assert metrics.total_norm.item() == pytest.approx(5.0)
    assert metrics.clip_coefficient.item() == pytest.approx(1.0)
    assert metrics.clipped.item() == 0.0


def test_clips_global_l2_norm() -> None:
    parameter = parameter_with_grad([3.0, 4.0])

    metrics = clip_grad_norm_mean_units([parameter], max_norm=1.0)

    assert metrics.total_norm.item() == pytest.approx(5.0)
    assert metrics.clip_coefficient.item() == pytest.approx(0.2)
    assert metrics.clipped.item() == 1.0
    assert torch.linalg.vector_norm(parameter.grad).item() == pytest.approx(1.0)


def test_summed_gradient_scale_uses_mean_gradient_threshold() -> None:
    parameter = parameter_with_grad([24.0, 32.0])

    metrics = clip_grad_norm_mean_units(
        [parameter],
        max_norm=1.0,
        summed_gradient_scale=8.0,
    )

    assert metrics.total_norm.item() == pytest.approx(5.0)
    assert metrics.clip_coefficient.item() == pytest.approx(0.2)
    assert metrics.clipped.item() == 1.0
    assert torch.linalg.vector_norm(parameter.grad).item() == pytest.approx(8.0)


@pytest.mark.parametrize(
    ("max_norm", "summed_gradient_scale"),
    [(0.0, 1.0), (-1.0, 1.0), (1.0, 0.0), (1.0, -1.0)],
)
def test_rejects_nonpositive_scales(max_norm: float, summed_gradient_scale: float) -> None:
    with pytest.raises(ValueError):
        clip_grad_norm_mean_units(
            [],
            max_norm=max_norm,
            summed_gradient_scale=summed_gradient_scale,
        )
