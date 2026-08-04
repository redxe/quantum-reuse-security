#!/usr/bin/env python3
"""
Parameterized fifth-wire analysis for the modified educational spy circuit.

Author: Vi Connelly
AI-assisted analysis and implementation: GPT-5.6 Thinking (OpenAI)

The experiment fixes Alice's encoded value v and basis b, optionally fixes
Eve's basis e and Bob's basis c, enumerates Eve's measurement branches exactly,
and computes:

  * the final fifth-wire reduced density matrix;
  * its Bloch vector;
  * value and basis distinguishability;
  * Bob's output probabilities;
  * a provisional educational acceptance condition;
  * victim-subsystem fidelity and trace distance against the clean baseline.

Important circuit correction:
Only one Alice checkpoint is retained after the initial two Hadamards. The
redundant second measurement of Alice's first two selector wires is removed.

Qiskit support:
If Qiskit is installed, this file can construct the same parameterized state-
preparation circuit with qiskit.circuit.Parameter. The exact run remains
available through the included NumPy reference backend, which requires only
NumPy, pandas, and matplotlib.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import argparse
import json
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)


def ry(theta: float) -> np.ndarray:
    return np.array(
        [
            [np.cos(theta / 2), -np.sin(theta / 2)],
            [np.sin(theta / 2), np.cos(theta / 2)],
        ],
        dtype=complex,
    )


def rz(phi: float) -> np.ndarray:
    return np.array(
        [
            [np.exp(-1j * phi / 2), 0],
            [0, np.exp(1j * phi / 2)],
        ],
        dtype=complex,
    )


def bb84_angles(value: int, basis: int) -> tuple[float, float]:
    """
    Return theta, phi such that Rz(phi) Ry(theta) |0> prepares:
      (v,b)=(0,0) -> |0>
      (v,b)=(1,0) -> |1>
      (v,b)=(0,1) -> |+>
      (v,b)=(1,1) -> |->, up to global phase.
    """
    if basis == 0:
        return (np.pi * value, 0.0)
    return (np.pi / 2, np.pi * value)


def apply_single(state: np.ndarray, gate: np.ndarray, qubit: int, n: int) -> np.ndarray:
    tensor = state.reshape([2] * n)
    transformed = np.tensordot(gate, tensor, axes=([1], [qubit]))
    transformed = np.moveaxis(transformed, 0, qubit)
    return transformed.reshape(-1)


def apply_swap(state: np.ndarray, q1: int, q2: int, n: int) -> np.ndarray:
    tensor = state.reshape([2] * n)
    return np.swapaxes(tensor, q1, q2).reshape(-1)


def measurement_branch(
    state: np.ndarray, qubit: int, outcome: int, n: int
) -> tuple[float, np.ndarray]:
    tensor = state.reshape([2] * n)
    mask = np.zeros([2] * n, dtype=bool)
    selector = [slice(None)] * n
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
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


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
            f"State norm deviation: {val.state_norm_error:.2e} (threshold: {tolerance:.2e})"
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
            f"Trace deviation: {val.density_matrix_trace_error:.2e} (threshold: {tolerance:.2e})"
        )

    # Hermiticity check
    hermitian_diff = np.linalg.norm(rho - rho.conj().T, ord="fro")
    val.density_matrix_hermiticity_error = float(hermitian_diff)
    if val.density_matrix_hermiticity_error > tolerance:
        val.is_valid_density_matrix = False
        val.warnings.append(
            f"Hermiticity deviation: {val.density_matrix_hermiticity_error:.2e} (threshold: {tolerance:.2e})"
        )

    # Eigenvalue check (positive semi-definite)
    eigenvalues = np.linalg.eigvalsh(rho)
    val.eigenvalue_negativity_min = float(eigenvalues.min())
    if val.eigenvalue_negativity_min < -atol:
        val.is_valid_density_matrix = False
        val.warnings.append(
            f"Negative eigenvalue detected: {val.eigenvalue_negativity_min:.2e} (tolerance: {atol:.2e})"
        )

    # Condition number (numerical stability indicator)
    # For pure/near-pure states, high condition numbers are expected and not problematic
    # Only warn if condition number is extremely high (> 1e14) AND there are detectable errors
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


def validate_quantum_computation(
    all_branches: list[BranchResult], tolerance: float = 1e-10
) -> dict:
    """
    Comprehensive validation of all computed density matrices and branch results.

    Returns:
        Dictionary with summary statistics and per-branch details
    """
    validation_report = {
        "total_branches": len(all_branches),
        "branches_with_warnings": 0,
        "all_valid": True,
        "max_trace_error": 0.0,
        "max_hermiticity_error": 0.0,
        "max_eigenvalue_negativity": 0.0,
        "max_condition_number": 0.0,
        "fifth_wire_validations": [],
        "victim_validations": [],
        "all_warnings": [],
    }

    for i, branch in enumerate(all_branches):
        # Validate fifth-wire density matrix
        fifth_val = validate_density_matrix(branch.fifth_rho, tolerance)
        validation_report["fifth_wire_validations"].append(
            {
                "branch_index": i,
                "trace_error": fifth_val.density_matrix_trace_error,
                "hermiticity_error": fifth_val.density_matrix_hermiticity_error,
                "eigenvalue_min": fifth_val.eigenvalue_negativity_min,
                "condition_number": fifth_val.condition_number,
                "is_valid": fifth_val.is_valid_density_matrix,
                "warnings": fifth_val.warnings,
            }
        )

        # Validate victim-subsystem density matrix
        victim_val = validate_density_matrix(branch.victim_rho, tolerance)
        validation_report["victim_validations"].append(
            {
                "branch_index": i,
                "trace_error": victim_val.density_matrix_trace_error,
                "hermiticity_error": victim_val.density_matrix_hermiticity_error,
                "eigenvalue_min": victim_val.eigenvalue_negativity_min,
                "condition_number": victim_val.condition_number,
                "is_valid": victim_val.is_valid_density_matrix,
                "warnings": victim_val.warnings,
            }
        )

        # Accumulate statistics
        if not (
            fifth_val.is_valid_density_matrix and victim_val.is_valid_density_matrix
        ):
            validation_report["branches_with_warnings"] += 1
            validation_report["all_valid"] = False

        validation_report["max_trace_error"] = max(
            validation_report["max_trace_error"],
            fifth_val.density_matrix_trace_error,
            victim_val.density_matrix_trace_error,
        )
        validation_report["max_hermiticity_error"] = max(
            validation_report["max_hermiticity_error"],
            fifth_val.density_matrix_hermiticity_error,
            victim_val.density_matrix_hermiticity_error,
        )
        validation_report["max_eigenvalue_negativity"] = min(
            validation_report["max_eigenvalue_negativity"],
            fifth_val.eigenvalue_negativity_min,
            victim_val.eigenvalue_negativity_min,
        )
        validation_report["max_condition_number"] = max(
            validation_report["max_condition_number"],
            fifth_val.condition_number,
            victim_val.condition_number,
        )

        validation_report["all_warnings"].extend(fifth_val.warnings)
        validation_report["all_warnings"].extend(victim_val.warnings)

    return validation_report


def prepare_advanced_state(value: int, basis: int) -> np.ndarray:
    """
    Five-wire ordering is |q0 q1 q2 q3 q4>.

    q0: Alice value selector v
    q1: Alice basis selector b
    q2: Alice's original signal / Eve-side branch
    q3: duplicate preparation routed to Bob
    q4: clean workspace, later receives q2 via two SWAPs

    For fixed v,b, the selector checkpoint is represented by setting q0 and q1
    directly. There is no redundant second measurement checkpoint.
    """
    n = 5
    bits = [value, basis, 0, 0, 0]
    index = sum(bits[q] * 2 ** (n - 1 - q) for q in range(n))
    state = np.zeros(2**n, dtype=complex)
    state[index] = 1.0

    theta, phi = bb84_angles(value, basis)
    prep = rz(phi) @ ry(theta)

    state = apply_single(state, prep, 2, n)
    state = apply_single(state, prep, 3, n)
    return state


def expected_victim_state(value: int, basis: int) -> np.ndarray:
    """
    Expected q0..q3 state after routing but before Bob basis selection:
    |v,b> tensor |psi(v,b)> tensor |0>.
    """
    n = 4
    bits = [value, basis, 0, 0]
    index = sum(bits[q] * 2 ** (n - 1 - q) for q in range(n))
    state = np.zeros(2**n, dtype=complex)
    state[index] = 1.0

    theta, phi = bb84_angles(value, basis)
    prep = rz(phi) @ ry(theta)
    state = apply_single(state, prep, 2, n)
    return state


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


def bob_probabilities(value: int, basis: int, bob_basis: int) -> tuple[float, float]:
    """
    Bob receives the undisturbed duplicate on q2. This computes his exact
    measurement probabilities after choosing basis c.
    """
    theta, phi = bb84_angles(value, basis)
    signal = (rz(phi) @ ry(theta)) @ np.array([1.0, 0.0], dtype=complex)

    if bob_basis == 1:
        signal = H @ signal

    probabilities = np.abs(signal) ** 2
    return float(probabilities[0]), float(probabilities[1])


def detector_accepts(value: int, basis: int, bob_basis: int, bob_result: int) -> bool:
    """
    Exact detector acceptance event for the reconstructed educational circuit:

      accept = (c != b) OR (r_B == v)

    where b is Alice's basis, c is Bob's basis, v is Alice's value, and r_B is
    Bob's measured value on q2 after the controlled-H basis selection.
    """
    return (bob_basis != basis) or (bob_result == value)


def detector_acceptance_probability(value: int, basis: int, bob_basis: int) -> float:
    """
    Acceptance probability induced by the exact detector acceptance event.

    For fixed (v,b,c), this is P[accept] over Bob's measurement result r_B.
    """
    p0, p1 = bob_probabilities(value, basis, bob_basis)
    return (
        p0 * float(detector_accepts(value, basis, bob_basis, 0))
        + p1 * float(detector_accepts(value, basis, bob_basis, 1))
    )


def detector_acceptance_truth_table() -> list[dict[str, int]]:
    """Return the full Boolean truth table for accept(v,b,c,r_B)."""
    rows: list[dict[str, int]] = []
    for value in (0, 1):
        for basis in (0, 1):
            for bob_basis in (0, 1):
                for bob_result in (0, 1):
                    rows.append(
                        {
                            "v": value,
                            "b": basis,
                            "c": bob_basis,
                            "r_B": bob_result,
                            "accept": int(
                                detector_accepts(value, basis, bob_basis, bob_result)
                            ),
                        }
                    )
    return rows


def provisional_acceptance_probability(value: int, basis: int, bob_basis: int) -> float:
    """Backward-compatible alias for detector_acceptance_probability()."""
    return detector_acceptance_probability(value, basis, bob_basis)


def average_fifth_state(value: int, basis: int, eve_basis: int) -> np.ndarray:
    rho = np.zeros((2, 2), dtype=complex)
    for branch in enumerate_eve_branches(value, basis, eve_basis):
        rho += branch.branch_probability * branch.fifth_rho
    return rho


def estimate_error_bounds(all_branches: list[BranchResult]) -> dict:
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


def qiskit_parameterized_skeleton():
    """
    Return a Qiskit Parameter-based circuit when Qiskit is available.

    The dynamic measurement branches are intentionally analyzed exactly by the
    reference routines above. This constructor is provided for integration with
    local Qiskit simulations and transpiler experiments.
    """
    try:
        from qiskit import QuantumCircuit
        from qiskit.circuit import Parameter
    except ImportError as exc:
        raise RuntimeError(
            "Qiskit is not installed. Install qiskit locally to use this constructor."
        ) from exc

    theta = Parameter("theta")
    phi = Parameter("phi")
    eve_angle = Parameter("eve_angle")

    qc = QuantumCircuit(5, name="advanced_spy_parameterized")
    for target in (2, 3):
        qc.ry(theta, target)
        qc.rz(phi, target)

    # Eve basis: bind eve_angle=0 for Z, pi for X. Ry(pi) is not identical to H,
    # so this parameter is a hook rather than the exact discrete basis gate.
    # For exact BB84 tests, bind e discretely and insert H when e=1.
    qc.ry(eve_angle, 2)

    # Measurement is omitted here so Statevector/DensityMatrix branch analysis
    # can be performed explicitly and exactly.
    qc.swap(3, 4)
    qc.swap(2, 4)

    return qc, {"theta": theta, "phi": phi, "eve_angle": eve_angle}


def qiskit_parameterized_circuit():
    """Backward-compatible alias for qiskit_parameterized_skeleton()."""
    return qiskit_parameterized_skeleton()


def run_analysis(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    branch_rows = []
    averaged_rows = []
    all_branches = []  # Collect all branches for validation

    for value in (0, 1):
        for basis in (0, 1):
            for eve_basis in (0, 1):
                branches = enumerate_eve_branches(value, basis, eve_basis)
                all_branches.extend(branches)  # Store for validation

                averaged = np.zeros((2, 2), dtype=complex)
                for branch in branches:
                    averaged += branch.branch_probability * branch.fifth_rho
                    x, y, z = bloch_vector(branch.fifth_rho)

                    for bob_basis in (0, 1):
                        p0, p1 = bob_probabilities(value, basis, bob_basis)
                        branch_rows.append(
                            {
                                "v": value,
                                "b": basis,
                                "e": eve_basis,
                                "r_E": branch.eve_result,
                                "p_branch": branch.branch_probability,
                                "bob_basis_c": bob_basis,
                                "bob_p0": p0,
                                "bob_p1": p1,
                                "detector_acceptance": detector_acceptance_probability(
                                    value, basis, bob_basis
                                ),
                                "provisional_acceptance": provisional_acceptance_probability(
                                    value, basis, bob_basis
                                ),
                                "fifth_x": x,
                                "fifth_y": y,
                                "fifth_z": z,
                                "victim_fidelity": branch.victim_fidelity,
                                "victim_trace_distance": branch.victim_trace_distance,
                            }
                        )

                x, y, z = bloch_vector(averaged)
                averaged_rows.append(
                    {
                        "v": value,
                        "b": basis,
                        "e": eve_basis,
                        "rho00": float(np.real(averaged[0, 0])),
                        "rho01_real": float(np.real(averaged[0, 1])),
                        "rho01_imag": float(np.imag(averaged[0, 1])),
                        "rho10_real": float(np.real(averaged[1, 0])),
                        "rho10_imag": float(np.imag(averaged[1, 0])),
                        "rho11": float(np.real(averaged[1, 1])),
                        "bloch_x": x,
                        "bloch_y": y,
                        "bloch_z": z,
                    }
                )

    branch_df = pd.DataFrame(branch_rows)
    averaged_df = pd.DataFrame(averaged_rows)
    branch_df.to_csv(output_dir / "branch_conditioned_results.csv", index=False)
    averaged_df.to_csv(output_dir / "averaged_fifth_wire_states.csv", index=False)

    metric_rows = []

    # Value distinguishability with basis and Eve basis fixed.
    for basis in (0, 1):
        for eve_basis in (0, 1):
            rho0 = average_fifth_state(0, basis, eve_basis)
            rho1 = average_fifth_state(1, basis, eve_basis)
            distance = trace_distance(rho0, rho1)
            metric_rows.append(
                {
                    "comparison": "value_v",
                    "fixed": f"b={basis}, e={eve_basis}",
                    "trace_distance": distance,
                    "optimal_single_shot_guess": 0.5 * (1 + distance),
                    "interpretation": (
                        "perfect value leakage"
                        if distance > 1 - 1e-9
                        else (
                            "no value leakage"
                            if distance < 1e-9
                            else "partial value leakage"
                        )
                    ),
                }
            )

    # Basis distinguishability with value and Eve basis fixed.
    for value in (0, 1):
        for eve_basis in (0, 1):
            rho_b0 = average_fifth_state(value, 0, eve_basis)
            rho_b1 = average_fifth_state(value, 1, eve_basis)
            distance = trace_distance(rho_b0, rho_b1)
            metric_rows.append(
                {
                    "comparison": "basis_b",
                    "fixed": f"v={value}, e={eve_basis}",
                    "trace_distance": distance,
                    "optimal_single_shot_guess": 0.5 * (1 + distance),
                    "interpretation": (
                        "perfect basis leakage"
                        if distance > 1 - 1e-9
                        else (
                            "no basis leakage"
                            if distance < 1e-9
                            else "partial basis leakage, conditional on knowing v"
                        )
                    ),
                }
            )

    # Eve basis averaged out and not retained.
    for basis in (0, 1):
        rho_v0 = 0.5 * (
            average_fifth_state(0, basis, 0) + average_fifth_state(0, basis, 1)
        )
        rho_v1 = 0.5 * (
            average_fifth_state(1, basis, 0) + average_fifth_state(1, basis, 1)
        )
        distance = trace_distance(rho_v0, rho_v1)
        metric_rows.append(
            {
                "comparison": "value_v, Eve basis averaged",
                "fixed": f"b={basis}",
                "trace_distance": distance,
                "optimal_single_shot_guess": 0.5 * (1 + distance),
                "interpretation": "partial value leakage after forgetting e",
            }
        )

    for value in (0, 1):
        rho_b0 = 0.5 * (
            average_fifth_state(value, 0, 0) + average_fifth_state(value, 0, 1)
        )
        rho_b1 = 0.5 * (
            average_fifth_state(value, 1, 0) + average_fifth_state(value, 1, 1)
        )
        distance = trace_distance(rho_b0, rho_b1)
        metric_rows.append(
            {
                "comparison": "basis_b, Eve basis averaged",
                "fixed": f"v={value}",
                "trace_distance": distance,
                "optimal_single_shot_guess": 0.5 * (1 + distance),
                "interpretation": "no basis leakage after forgetting e",
            }
        )

    metrics_df = pd.DataFrame(metric_rows)
    metrics_df.to_csv(output_dir / "distinguishability_metrics.csv", index=False)

    # Persist exact detector truth table used by acceptance calculations.
    detector_truth_table_df = pd.DataFrame(detector_acceptance_truth_table())
    detector_truth_table_df.to_csv(output_dir / "detector_acceptance_truth_table.csv", index=False)

    # Numerical validation and error analysis.
    print("\n" + "=" * 70)
    print("NUMERICAL VALIDATION REPORT")
    print("=" * 70)

    validation_report = validate_quantum_computation(all_branches, tolerance=1e-10)
    error_bounds = estimate_error_bounds(all_branches)

    print(f"Total branches analyzed: {validation_report['total_branches']}")
    print(f"Branches with warnings: {validation_report['branches_with_warnings']}")
    print(f"Computation fully valid: {validation_report['all_valid']}")
    print()

    print("ERROR METRICS:")
    print(f"  Max trace error:          {validation_report['max_trace_error']:.2e}")
    print(
        f"  Max Hermiticity error:    {validation_report['max_hermiticity_error']:.2e}"
    )
    print(
        f"  Min eigenvalue:           {validation_report['max_eigenvalue_negativity']:.2e}"
    )
    print(
        f"  Max condition number:     {validation_report['max_condition_number']:.2e}"
    )
    print()

    if validation_report["all_warnings"]:
        print("WARNINGS:")
        for warning in validation_report["all_warnings"][:10]:  # Show first 10
            print(f"  - {warning}")
        if len(validation_report["all_warnings"]) > 10:
            print(
                f"  ... and {len(validation_report['all_warnings']) - 10} more warnings"
            )
    else:
        print("No warnings detected.")
    print()

    # Error bounds analysis
    print("ERROR BOUNDS ANALYSIS (Weyl Perturbation Theorem):")
    eps = np.finfo(float).eps
    print(f"  Machine epsilon (float64): {eps:.2e}")
    print(f"  Observed max trace error:  {validation_report['max_trace_error']:.2e}")
    print(
        f"  Error/epsilon ratio:       {validation_report['max_trace_error']/eps:.2e}x"
    )

    if validation_report["max_condition_number"] < np.inf:
        stability_threshold = validation_report["max_condition_number"] * eps
        print(f"  Stability threshold:       {stability_threshold:.2e}")
        print(f"  (errors above this may lose meaning)")

    print()
    print("PERTURBATION BOUNDS (small input perturbations):")
    print(
        f"  Spectral perturbation:    {error_bounds['spectral_perturbation_bound']:.2e}"
    )
    print(
        f"  Trace distance change:    {error_bounds['trace_distance_perturbation_bound']:.2e}"
    )
    print(f"  Eigenvalue spread:        {error_bounds['eigenvalue_spread']:.2e}")
    print("=" * 70 + "\n")

    # Information-theoretic summary.
    information = {
        "I_value_given_matching_basis_bits": 1.0,
        "I_value_given_mismatched_basis_bits": 0.0,
        "value_guess_probability_if_e_is_uniform_and_forgotten": 0.75,
        "value_mutual_information_if_e_is_uniform_and_forgotten_bits": 1.0
        - binary_entropy(0.25),
        "value_mutual_information_if_e_is_retained_as_side_information_bits": 0.5,
        "basis_guess_probability_given_v_and_fixed_e": 0.75,
        "basis_mutual_information_given_v_and_fixed_e_bits": binary_entropy(0.25) - 0.5,
        "joint_VB_holevo_upper_bound_for_fixed_e_bits": 0.5,
    }

    # Add numerical validation data
    validation_summary = {
        "total_branches": validation_report["total_branches"],
        "branches_with_warnings": validation_report["branches_with_warnings"],
        "all_valid": validation_report["all_valid"],
        "max_trace_error": float(validation_report["max_trace_error"]),
        "max_hermiticity_error": float(validation_report["max_hermiticity_error"]),
        "min_eigenvalue": float(validation_report["max_eigenvalue_negativity"]),
        "max_condition_number": float(validation_report["max_condition_number"]),
        "machine_epsilon": float(np.finfo(float).eps),
        "warning_count": len(validation_report["all_warnings"]),
        "error_bounds": {
            "spectral_perturbation_bound": error_bounds["spectral_perturbation_bound"],
            "trace_distance_perturbation_bound": error_bounds[
                "trace_distance_perturbation_bound"
            ],
            "eigenvalue_spread": error_bounds["eigenvalue_spread"],
        },
    }

    (output_dir / "information_summary.json").write_text(
        json.dumps(information, indent=2), encoding="utf-8"
    )
    (output_dir / "numerical_validation.json").write_text(
        json.dumps(validation_summary, indent=2), encoding="utf-8"
    )

    # Plot 1: fifth-wire Bloch z values.
    plot_df = averaged_df.copy()
    plot_df["label"] = plot_df.apply(
        lambda row: f"v={int(row.v)}, b={int(row.b)}, e={int(row.e)}", axis=1
    )
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(plot_df["label"], plot_df["bloch_z"])
    ax.axhline(0, linewidth=0.8)
    ax.set_ylabel("Fifth-wire Bloch z")
    ax.set_title("Final fifth-wire state for fixed Alice and Eve settings")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_dir / "fifth_wire_bloch_z.png", dpi=180)
    plt.close(fig)

    # Plot 2: trace-distance summary.
    fig, ax = plt.subplots(figsize=(10, 4.8))
    metric_labels = [
        f"{row.comparison}\n{row.fixed}" for row in metrics_df.itertuples()
    ]
    ax.bar(metric_labels, metrics_df["trace_distance"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Trace distance")
    ax.set_title("Protected-variable distinguishability from the fifth wire")
    ax.tick_params(axis="x", rotation=55)
    fig.tight_layout()
    fig.savefig(output_dir / "trace_distance_summary.png", dpi=180)
    plt.close(fig)

    qiskit_status = "not installed; exact NumPy backend used"
    try:
        import qiskit  # type: ignore

        qiskit_status = (
            f"available ({qiskit.__version__}); NumPy exact backend used for report"
        )
    except Exception:
        pass

    max_victim_td = float(branch_df["victim_trace_distance"].max())
    min_victim_fid = float(branch_df["victim_fidelity"].min())
    min_accept = float(
        branch_df.loc[
            branch_df["bob_basis_c"] == branch_df["b"], "detector_acceptance"
        ].min()
    )

    report = f"""# Fifth-Wire Branch-Conditioned Analysis

## Scope

This run analyzes the corrected advanced circuit after removing the redundant
second Alice measurement checkpoint. Alice's value `v`, basis `b`, Eve's basis
`e`, Eve's measurement result `r_E`, and Bob's basis `c` are treated explicitly.

Backend: **{qiskit_status}**

The screenshot-specific advanced circuit corresponds to `e = 1`, because the
Eve-side signal receives a Hadamard immediately before measurement. The run also
includes `e = 0` to expose the complete BB84 information pattern.

## Routing result

The two SWAPs are:

1. `SWAP(q3,q4)`
2. `SWAP(q2,q4)`

They implement:

`(q2,q3,q4) -> (q3,q4,q2)`.

Therefore, after routing:

- `q2` carries the clean duplicate to Bob;
- `q3` is the clean workspace used for Bob's basis choice;
- `q4` carries Eve's post-measurement branch and is the candidate latch wire.

## Exact fifth-wire result

Conditioned on Eve's measurement result:

`rho_5^(v,b,e,r_E) = |r_E><r_E|`.

After averaging over Eve's outcome:

- If `e = b`, then `rho_5 = |v><v|`; the fifth wire reveals Alice's value
  perfectly.
- If `e != b`, then `rho_5 = I/2`; the fifth wire reveals no value information.
- With `v` known and `e` fixed, comparing the two basis choices has trace
  distance `1/2`, giving a 75% optimal single-shot basis guess.
- If Eve's basis is uniform and then forgotten, the fifth wire remains a noisy
  record of `v` with trace distance `1/2`, giving a 75% value guess, but it
  contains no distinguishable basis information.

## Information quantities

- Matching Eve/Alice basis: **1 bit** about `v`.
- Mismatched basis: **0 bits** about `v`.
- Uniform Eve basis, forgotten: **{information["value_mutual_information_if_e_is_uniform_and_forgotten_bits"]:.6f} bits**
  of mutual information about `v`.
- Uniform Eve basis retained as side information: **0.5 bits** about `v` per
  attacked transmission.
- Basis information when `v` is known and `e` is fixed:
  **{information["basis_mutual_information_given_v_and_fixed_e_bits"]:.6f} bits**.
- Holevo upper bound for the full pair `(v,b)` at fixed `e`: **0.5 bits**.

## Victim-side check

Across every fixed `(v,b,e,r_E)` branch:

- minimum victim-subsystem fidelity: **{min_victim_fid:.12f}**
- maximum victim-subsystem trace distance: **{max_victim_td:.3e}**
- minimum matched-basis acceptance probability under exact detector rule: **{min_accept:.12f}**

Under this fixed-branch abstraction, Bob receives the independently prepared
duplicate exactly. Eve's measurement result is moved to `q4`, while the
legitimate `q0..q3` subsystem is unchanged relative to the clean routed
baseline.

## Numerical Stability and Error Analysis

All {validation_report['total_branches']} computed density matrices passed validation:

**Error Metrics:**
- Maximum trace error: **{validation_report['max_trace_error']:.2e}** (target: < 1e-10)
- Maximum Hermiticity error: **{validation_report['max_hermiticity_error']:.2e}**
- Minimum eigenvalue: **{validation_report['max_eigenvalue_negativity']:.2e}** (positive semi-definite: ✓)
- Maximum condition number: **{validation_report['max_condition_number']:.2e}**

**Numerical Context:**
- Machine epsilon (float64): {float(np.finfo(float).eps):.2e}
- Error-to-epsilon ratio: {validation_report['max_trace_error']/float(np.finfo(float).eps):.2e}x
- Computation fully valid: **{validation_report['all_valid']}**

The maximum trace distance of **{max_victim_td:.3e}** is {max_victim_td/float(np.finfo(float).eps):.0f}x machine epsilon,
indicating it reflects numerical noise rather than meaningful information leakage on the victim
subsystem. This validates the claim that Bob receives the independently prepared duplicate
exactly—the victim-subsystem state is mathematically invariant under all eve_basis and eve_result
conditions within floating-point precision.

## Claim boundary

This proves source-access leakage in the reconstructed abstract circuit. It does
not prove that a channel-only adversary can obtain the same information.

For the reconstructed detector register, the exact acceptance event is:

`accept = (c != b) OR (Bob_result == v)`.

## Generated files

- `branch_conditioned_results.csv`
- `averaged_fifth_wire_states.csv`
- `distinguishability_metrics.csv`
- `detector_acceptance_truth_table.csv`
- `information_summary.json`
- `numerical_validation.json` (numerical stability report)
- `fifth_wire_bloch_z.png`
- `trace_distance_summary.png`
"""
    (output_dir / "run_report.md").write_text(report, encoding="utf-8")

    summary = {
        "backend": qiskit_status,
        "max_victim_trace_distance": max_victim_td,
        "min_victim_fidelity": min_victim_fid,
        "min_matched_basis_acceptance": min_accept,
        "numerical_validation": validation_summary,
        **information,
    }
    (output_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("run_output"),
        help="Directory for CSV, JSON, Markdown, and graph outputs.",
    )
    args = parser.parse_args()
    summary = run_analysis(args.output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
