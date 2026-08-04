"""Information and distinguishability metrics."""

from __future__ import annotations

import math

import numpy as np


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    delta = (rho - sigma + (rho - sigma).conj().T) / 2
    return float(0.5 * np.sum(np.abs(np.linalg.eigvalsh(delta))))


def fidelity_with_pure(rho: np.ndarray, pure_state: np.ndarray) -> float:
    return float(np.real(np.vdot(pure_state, rho @ pure_state)))


def bloch_vector(rho: np.ndarray) -> tuple[float, float, float]:
    pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
    pauli_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    pauli_z = np.array([[1, 0], [0, -1]], dtype=complex)
    return tuple(
        float(np.real(np.trace(rho @ pauli))) for pauli in (pauli_x, pauli_y, pauli_z)
    )


def binary_entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


__all__ = ["binary_entropy", "bloch_vector", "fidelity_with_pure", "trace_distance"]
