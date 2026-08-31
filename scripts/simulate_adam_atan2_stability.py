#!/usr/bin/env python3
"""Compare AdamATan2 stability guards under controlled gradient spikes.

This is an optimizer-state simulation, not a model-training replay. It uses the
repository's AdamATan2 equations and reports deviation from an identical clean
gradient stream after injecting either a single or sustained directional
outlier.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import torch


@dataclass
class OptimizerState:
    parameter: torch.Tensor
    first_moment: torch.Tensor
    second_moment: torch.Tensor
    step: int = 0


@dataclass(frozen=True)
class Strategy:
    name: str
    raw_clip_norm: float | None = None
    skip_norm: float | None = None
    update_clip_rms: float | None = None
    backoff_trigger_norm: float | None = None
    backoff_factor: float = 1.0
    backoff_steps: int = 0


def unit_vector(generator: torch.Generator, dimensions: int) -> torch.Tensor:
    value = torch.randn(dimensions, generator=generator, dtype=torch.float64)
    return value / torch.linalg.vector_norm(value)


def gradient_stream(
    *, steps: int, dimensions: int, normal_norm: float, seed: int
) -> list[torch.Tensor]:
    generator = torch.Generator().manual_seed(seed)
    direction = unit_vector(generator, dimensions)
    gradients: list[torch.Tensor] = []
    correlation = 0.95
    innovation_scale = math.sqrt(1 - correlation**2)
    for _ in range(steps):
        innovation = unit_vector(generator, dimensions)
        direction = correlation * direction + innovation_scale * innovation
        direction /= torch.linalg.vector_norm(direction)
        gradients.append(direction * normal_norm)
    return gradients


def inject_spike(
    clean: list[torch.Tensor],
    *,
    start: int,
    length: int,
    spike_norm: float,
    mode: str,
    seed: int,
) -> list[torch.Tensor]:
    gradients = [gradient.clone() for gradient in clean]
    generator = torch.Generator().manual_seed(seed)
    for step in range(start, start + length):
        if mode == "coherent":
            direction = clean[step] / torch.linalg.vector_norm(clean[step])
        elif mode == "corrupted":
            direction = unit_vector(generator, clean[step].numel())
        else:
            raise ValueError(f"Unknown spike mode: {mode}")
        gradients[step] = direction * spike_norm
    return gradients


def adam_atan2_step(
    state: OptimizerState,
    gradient: torch.Tensor,
    *,
    learning_rate: float,
    beta1: float,
    beta2: float,
    update_clip_rms: float | None,
) -> tuple[float, float]:
    state.step += 1
    state.first_moment.lerp_(gradient, 1 - beta1)
    state.second_moment.mul_(beta2).addcmul_(gradient, gradient, value=1 - beta2)
    bias_correction1 = 1 - beta1**state.step
    bias_correction2 = 1 - beta2**state.step
    denominator = state.second_moment.sqrt() / math.sqrt(bias_correction2)
    direction = torch.atan2(state.first_moment, denominator) / bias_correction1
    update_rms_before = direction.square().mean().sqrt().item()
    coefficient = 1.0
    if update_clip_rms is not None:
        coefficient = min(1.0, update_clip_rms / (update_rms_before + 1e-12))
    state.parameter.add_(direction, alpha=-learning_rate * coefficient)
    return update_rms_before, coefficient


def run_strategy(
    gradients: list[torch.Tensor],
    strategy: Strategy,
    *,
    learning_rate: float,
    beta1: float,
    beta2: float,
) -> tuple[list[torch.Tensor], list[torch.Tensor], list[float], int]:
    dimensions = gradients[0].numel()
    state = OptimizerState(
        parameter=torch.zeros(dimensions, dtype=torch.float64),
        first_moment=torch.zeros(dimensions, dtype=torch.float64),
        second_moment=torch.zeros(dimensions, dtype=torch.float64),
    )
    parameters: list[torch.Tensor] = []
    directions: list[torch.Tensor] = []
    update_rms_values: list[float] = []
    skipped = 0
    backoff_remaining = 0
    for gradient in gradients:
        raw_norm = torch.linalg.vector_norm(gradient).item()
        if strategy.backoff_trigger_norm is not None and raw_norm > strategy.backoff_trigger_norm:
            backoff_remaining = strategy.backoff_steps
        if strategy.skip_norm is not None and raw_norm > strategy.skip_norm:
            skipped += 1
            parameters.append(state.parameter.clone())
            directions.append(torch.zeros_like(state.parameter))
            update_rms_values.append(0.0)
            continue
        effective_gradient = gradient
        if strategy.raw_clip_norm is not None and raw_norm > strategy.raw_clip_norm:
            effective_gradient = gradient * (strategy.raw_clip_norm / raw_norm)
        step_lr = learning_rate
        if backoff_remaining > 0:
            step_lr *= strategy.backoff_factor
            backoff_remaining -= 1
        previous = state.parameter.clone()
        update_rms, _ = adam_atan2_step(
            state,
            effective_gradient,
            learning_rate=step_lr,
            beta1=beta1,
            beta2=beta2,
            update_clip_rms=strategy.update_clip_rms,
        )
        parameters.append(state.parameter.clone())
        directions.append((state.parameter - previous) / learning_rate)
        update_rms_values.append(update_rms)
    return parameters, directions, update_rms_values, skipped


def summarize(
    *,
    scenario: str,
    strategy: Strategy,
    parameters: list[torch.Tensor],
    directions: list[torch.Tensor],
    update_rms_values: list[float],
    clean_parameters: list[torch.Tensor],
    clean_directions: list[torch.Tensor],
    event_start: int,
    event_length: int,
    learning_rate: float,
    healthy_update_rms: float,
    skipped: int,
) -> dict[str, float | int | str | None]:
    end = event_start + event_length
    divergences = [
        (parameter - clean).square().mean().sqrt().item() / learning_rate
        for parameter, clean in zip(parameters, clean_parameters)
    ]
    parameter_before_event = parameters[event_start - 1]
    event_displacement = (
        parameters[end - 1] - parameter_before_event
    ).square().mean().sqrt().item() / learning_rate
    direction_errors = [
        (direction - clean).square().mean().sqrt().item()
        for direction, clean in zip(directions, clean_directions)
    ]
    recovery_step = None
    recovery_threshold = 0.1 * healthy_update_rms
    for step in range(end, len(direction_errors) - 9):
        if max(direction_errors[step : step + 10]) <= recovery_threshold:
            recovery_step = step - end + 1
            break
    return {
        "scenario": scenario,
        "strategy": strategy.name,
        "skipped_steps": skipped,
        "peak_update_rms": max(update_rms_values[event_start:]),
        "peak_direction_error_rms": max(direction_errors[event_start:]),
        "event_parameter_displacement_lr_units": event_displacement,
        "parameter_divergence_lr_units_at_event_end": divergences[end - 1],
        "final_parameter_divergence_lr_units": divergences[-1],
        "direction_recovery_steps": recovery_step,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dimensions", type=int, default=8192)
    parser.add_argument("--warmup-steps", type=int, default=400)
    parser.add_argument("--recovery-steps", type=int, default=400)
    parser.add_argument("--normal-norm", type=float, default=0.2)
    parser.add_argument("--spike-norm", type=float, default=200.0)
    parser.add_argument("--clip-norm", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    max_event_length = 100
    total_steps = args.warmup_steps + max_event_length + args.recovery_steps
    clean_gradients = gradient_stream(
        steps=total_steps,
        dimensions=args.dimensions,
        normal_norm=args.normal_norm,
        seed=1234,
    )
    clean_strategy = Strategy("clean")
    clean_parameters, clean_directions, clean_update_rms, _ = run_strategy(
        clean_gradients,
        clean_strategy,
        learning_rate=args.learning_rate,
        beta1=0.9,
        beta2=0.95,
    )
    healthy_window = torch.tensor(clean_update_rms[100 : args.warmup_steps])
    healthy_update_rms = healthy_window.median().item()
    update_clip_rms = torch.quantile(healthy_window, 0.99).item() * 1.10

    strategies = (
        Strategy("unguarded"),
        Strategy("raw_gradient_clip", raw_clip_norm=args.clip_norm),
        Strategy("skip_step", skip_norm=args.clip_norm),
        Strategy("update_rms_clip", update_clip_rms=update_clip_rms),
        Strategy(
            "temporary_lr_backoff",
            backoff_trigger_norm=args.clip_norm,
            backoff_factor=0.1,
            backoff_steps=250,
        ),
    )
    scenarios = (
        ("single_coherent", 1, "coherent"),
        ("single_corrupted", 1, "corrupted"),
        ("sustained_corrupted", 100, "corrupted"),
    )
    clean_references = {
        strategy.name: run_strategy(
            clean_gradients,
            strategy,
            learning_rate=args.learning_rate,
            beta1=0.9,
            beta2=0.95,
        )
        for strategy in strategies
    }
    rows: list[dict[str, float | int | str | None]] = []
    for scenario_name, event_length, mode in scenarios:
        gradients = inject_spike(
            clean_gradients,
            start=args.warmup_steps,
            length=event_length,
            spike_norm=args.spike_norm,
            mode=mode,
            seed=5678,
        )
        for strategy in strategies:
            reference_parameters, reference_directions, _, _ = clean_references[
                strategy.name
            ]
            parameters, directions, update_rms_values, skipped = run_strategy(
                gradients,
                strategy,
                learning_rate=args.learning_rate,
                beta1=0.9,
                beta2=0.95,
            )
            rows.append(
                summarize(
                    scenario=scenario_name,
                    strategy=strategy,
                    parameters=parameters,
                    directions=directions,
                    update_rms_values=update_rms_values,
                    clean_parameters=reference_parameters,
                    clean_directions=reference_directions,
                    event_start=args.warmup_steps,
                    event_length=event_length,
                    learning_rate=args.learning_rate,
                    healthy_update_rms=healthy_update_rms,
                    skipped=skipped,
                )
            )

    metadata = {
        "dimensions": args.dimensions,
        "normal_norm": args.normal_norm,
        "spike_norm": args.spike_norm,
        "gradient_guard_threshold": args.clip_norm,
        "healthy_update_rms_median": healthy_update_rms,
        "update_clip_rms": update_clip_rms,
        "learning_rate": args.learning_rate,
    }
    print(json.dumps({"metadata": metadata, "results": rows}, indent=2))
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"metadata": metadata, "results": rows}, indent=2) + "\n"
        )


if __name__ == "__main__":
    main()
