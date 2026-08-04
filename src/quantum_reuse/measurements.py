"""Measurement and reduced-state routines for branch-conditioned analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .circuits import H, apply_single, apply_swap
from .metrics import fidelity_with_pure, trace_distance
from .state_preparation import expected_victim_state, prepare_advanced_state


def measurement_branch(
    state: np.ndarray, qubit: int, outcome: int, n: int
) -> tuple[float, np.ndarray]:
    tensor = state.reshape([2] * n)
    mask = np.zeros([2] * n, dtype=bool)
    selector: list[object] = [slice(None)] * n
    selector[qubit] = outcome
    mask[tuple(selector)] = True

    projected = tensor.copy()
    projected[~mask] = 0
    probability = float(np.vdot(projected.reshape(-1), projected.reshape(-1)).real)

    if probability > 1e-15:
        projected /= np.sqrt(probability)

    return probability, projected.reshape(-1)


def reduced_density_pure(state: np.ndarray, keep: Iterable[int], n: int) -> np.ndarray:
    keep = list(keep)
    traced = [q for q in range(n) if q not in keep]
    tensor = state.reshape([2] * n)
    tensor = np.transpose(tensor, keep + traced)
    matrix = tensor.reshape(2 ** len(keep), 2 ** len(traced))
    return matrix @ matrix.conj().T


@dataclass
class BranchResult:
    value: int
    basis: int
    eve_basis: int
    eve_result: int
    branch_probability: float
    fifth_rho: np.ndarray
    victim_rho: np.ndarray
    victim_fidelity: float
    victim_trace_distance: float


def enumerate_eve_branches(
    value: int, basis: int, eve_basis: int
) -> list[BranchResult]:
    n = 5
    state = prepare_advanced_state(value, basis)

    # Eve measures q2 in Z (e=0) or X (e=1).
    if eve_basis == 1:
        state = apply_single(state, H, 2, n)

    results: list[BranchResult] = []
    target_victim = expected_victim_state(value, basis)
    target_victim_rho = np.outer(target_victim, target_victim.conj())

    for eve_result in (0, 1):
        probability, branch = measurement_branch(state, 2, eve_result, n)
        if probability < 1e-14:
            continue

        # Quirk routing:
        #   SWAP(q3,q4), then SWAP(q2,q4)
        # This maps semantic roles (q2,q3,q4) -> (q3,q4,q2).
        branch = apply_swap(branch, 3, 4, n)
        branch = apply_swap(branch, 2, 4, n)

        fifth_rho = reduced_density_pure(branch, [4], n)
        victim_rho = reduced_density_pure(branch, [0, 1, 2, 3], n)

        results.append(
            BranchResult(
                value=value,
                basis=basis,
                eve_basis=eve_basis,
                eve_result=eve_result,
                branch_probability=probability,
                fifth_rho=fifth_rho,
                victim_rho=victim_rho,
                victim_fidelity=fidelity_with_pure(victim_rho, target_victim),
                victim_trace_distance=trace_distance(victim_rho, target_victim_rho),
            )
        )

    return results


__all__ = [
    "BranchResult",
    "enumerate_eve_branches",
    "measurement_branch",
    "reduced_density_pure",
]
