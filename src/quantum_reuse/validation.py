"""Numerical validation routines for quantum states and density matrices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence

import numpy as np


class BranchLike(Protocol):
    fifth_rho: np.ndarray


def canonicalize_near_zero(value: float, atol: float = 1e-15) -> float:
    """Normalize semantically zero values for stable serialized summaries."""
    return 0.0 if abs(value) <= atol else value


def canonicalize_validation_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """Apply near-zero normalization to the serialized validation summary only."""
    normalized = dict(summary)
    if "min_eigenvalue" in normalized:
        normalized["min_eigenvalue"] = canonicalize_near_zero(
            float(normalized["min_eigenvalue"])
        )
    if "max_eigenvalue_negativity" in normalized:
        normalized["max_eigenvalue_negativity"] = canonicalize_near_zero(
            float(normalized["max_eigenvalue_negativity"])
        )
    return normalized


@dataclass
class NumericalValidation:
    """Track numerical stability metrics for quantum states and operators."""

    state_norm_error: float = 0.0
    density_matrix_trace_error: float = 0.0
    density_matrix_hermiticity_error: float = 0.0
    eigenvalue_negativity_min: float = 0.0
    condition_number: float = 0.0
    is_valid_state: bool = True
    is_valid_density_matrix: bool = True
    warnings: list[str] = field(default_factory=list)


def validate_pure_state(
    state: np.ndarray, tolerance: float = 1e-10
) -> NumericalValidation:
    """
    Validate that a state vector is properly normalized and check numerical stability.

    Parameters:
        state: 1D complex array representing a quantum state
        tolerance: acceptable deviation from unit norm

    Returns:
        NumericalValidation object with error metrics and warnings
    """
    val = NumericalValidation()
    norm_squared = float(np.vdot(state, state).real)
    val.state_norm_error = abs(norm_squared - 1.0)

    if val.state_norm_error > tolerance:
        val.is_valid_state = False
        val.warnings.append(
            "State norm deviation: "
            f"{val.state_norm_error:.2e} (threshold: {tolerance:.2e})"
        )

    return val


def validate_density_matrix(
    rho: np.ndarray, tolerance: float = 1e-10, atol: float = 1e-14
) -> NumericalValidation:
    """
    Validate density matrix properties: trace=1, Hermitian, positive semi-definite.

    Parameters:
        rho: 2D complex array representing a density matrix
        tolerance: acceptable deviation from trace=1 and Hermiticity
        atol: absolute tolerance for eigenvalue negativity check

    Returns:
        NumericalValidation object with comprehensive error metrics
    """
    val = NumericalValidation()

    # Trace check
    trace = float(np.trace(rho).real)
    val.density_matrix_trace_error = abs(trace - 1.0)
    if val.density_matrix_trace_error > tolerance:
        val.is_valid_density_matrix = False
        val.warnings.append(
            "Trace deviation: "
            f"{val.density_matrix_trace_error:.2e} (threshold: {tolerance:.2e})"
        )

    # Hermiticity check
    hermitian_diff = np.linalg.norm(rho - rho.conj().T, ord="fro")
    val.density_matrix_hermiticity_error = float(hermitian_diff)
    if val.density_matrix_hermiticity_error > tolerance:
        val.is_valid_density_matrix = False
        val.warnings.append(
            "Hermiticity deviation: "
            f"{val.density_matrix_hermiticity_error:.2e} (threshold: {tolerance:.2e})"
        )

    # Eigenvalue check (positive semi-definite)
    eigenvalues = np.linalg.eigvalsh(rho)
    val.eigenvalue_negativity_min = float(eigenvalues.min())
    if val.eigenvalue_negativity_min < -atol:
        val.is_valid_density_matrix = False
        negativity = val.eigenvalue_negativity_min
        tolerance_text = f"(tolerance: {atol:.2e})"
        message = (
            "Negative eigenvalue detected: " f"{negativity:.2e} " f"{tolerance_text}"
        )
        val.warnings.append(message)

    # Condition number (numerical stability indicator)
    # For pure/near-pure states, high condition numbers are expected and not problematic
    # Only warn if condition number is extremely high (> 1e14)
    # and there are detectable errors.
    if eigenvalues.max() > 0:
        val.condition_number = float(eigenvalues.max() / max(eigenvalues.min(), 1e-16))
    else:
        val.condition_number = np.inf

    # Only warn about condition number if we're actually seeing errors that are
    # larger than what machine epsilon would allow
    eps = np.finfo(float).eps
    expected_error_floor = val.condition_number * eps
    if (
        val.condition_number > 1e14
        and val.density_matrix_trace_error > expected_error_floor * 10
    ):
        val.warnings.append(
            f"High condition number with detectable error: {val.condition_number:.2e}"
        )

    return val


def estimate_error_bounds(all_branches: Sequence[BranchLike]) -> dict[str, float]:
    """
    Estimate how results would change under small input perturbations.
    Useful for understanding sensitivity and stability of key claims.

    Returns:
        Dictionary with error bound estimates
    """
    eps = np.finfo(float).eps

    # Estimate spectral perturbation bounds
    all_eigenvalues = []
    all_traces = []

    for branch in all_branches:
        eigs = np.linalg.eigvalsh(branch.fifth_rho)
        trace = float(np.trace(branch.fifth_rho).real)
        all_eigenvalues.extend(eigs)
        all_traces.append(trace)

    all_eigenvalues = np.array(all_eigenvalues)

    # Weyl's perturbation theorem: eigenvalue changes scale with operator norm
    # For density matrices, operator norm is at most 1
    spectral_perturbation_bound = 1.0 * eps

    # Trace distance perturbation: scales with eigenvalue differences
    eigenvalue_spread = np.ptp(all_eigenvalues)  # peak-to-peak
    trace_distance_perturbation = eigenvalue_spread * eps

    return {
        "machine_epsilon": float(eps),
        "spectral_perturbation_bound": float(spectral_perturbation_bound),
        "trace_distance_perturbation_bound": float(trace_distance_perturbation),
        "eigenvalue_spread": float(eigenvalue_spread),
        "relative_error_tolerance": 1.0 * eps,  # 1 epsilon for relative errors
    }


__all__ = [
    "BranchLike",
    "NumericalValidation",
    "canonicalize_near_zero",
    "canonicalize_validation_summary",
    "estimate_error_bounds",
    "validate_density_matrix",
    "validate_pure_state",
]
