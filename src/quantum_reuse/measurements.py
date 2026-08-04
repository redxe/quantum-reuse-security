"""Measurement and reduced-state routines for branch-conditioned analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

import numpy as np

if TYPE_CHECKING:
    from .parameterized_fifth_wire_analysis import BranchResult


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


def enumerate_eve_branches(
    value: int, basis: int, eve_basis: int
) -> list["BranchResult"]:
    from .parameterized_fifth_wire_analysis import enumerate_eve_branches as _enumerate

    return _enumerate(value, basis, eve_basis)


def __getattr__(name: str):
    if name == "BranchResult":
        from .parameterized_fifth_wire_analysis import BranchResult

        return BranchResult
    raise AttributeError(name)


__all__ = [
    "BranchResult",
    "enumerate_eve_branches",
    "measurement_branch",
    "reduced_density_pure",
]
