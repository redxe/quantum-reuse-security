import numpy as np

from quantum_reuse.state_preparation import bb84_angles
from quantum_reuse.validation import (
    canonicalize_near_zero,
    estimate_error_bounds,
    validate_density_matrix,
    validate_pure_state,
)
from quantum_reuse.parameterized_fifth_wire_analysis import rz, ry


class _BranchLike:
    def __init__(self, rho: np.ndarray) -> None:
        self.fifth_rho = rho


def test_bb84_state_preparation() -> None:
    ket0 = np.array([1.0, 0.0], dtype=complex)
    plus = np.array([1.0, 1.0], dtype=complex) / np.sqrt(2)

    theta, phi = bb84_angles(0, 0)
    state = (rz(phi) @ ry(theta)) @ ket0
    assert np.allclose(state, ket0, atol=1e-12)

    theta, phi = bb84_angles(0, 1)
    state = (rz(phi) @ ry(theta)) @ ket0
    # Up to global phase, should match |+>.
    overlap = abs(np.vdot(state, plus))
    assert overlap > 1 - 1e-12


def test_density_matrix_validation() -> None:
    rho = np.array([[0.5, 0.0], [0.0, 0.5]], dtype=complex)
    result = validate_density_matrix(rho)
    assert result.is_valid_density_matrix
    assert result.density_matrix_trace_error < 1e-12


def test_density_matrix_validation_flags_malformed_inputs() -> None:
    non_hermitian = np.array([[0.5, 1.0], [0.0, 0.5]], dtype=complex)
    non_trace_one = np.array([[0.7, 0.0], [0.0, 0.1]], dtype=complex)
    negative_eigenvalue = np.array([[1.2, 0.0], [0.0, -0.2]], dtype=complex)

    hermitian_result = validate_density_matrix(non_hermitian)
    trace_result = validate_density_matrix(non_trace_one)
    eigen_result = validate_density_matrix(negative_eigenvalue)

    assert not hermitian_result.is_valid_density_matrix
    assert hermitian_result.density_matrix_hermiticity_error > 1e-12
    assert not trace_result.is_valid_density_matrix
    assert trace_result.density_matrix_trace_error > 1e-12
    assert not eigen_result.is_valid_density_matrix
    assert eigen_result.eigenvalue_negativity_min < 0.0


def test_pure_state_validation() -> None:
    state = np.array([1.0, 0.0], dtype=complex)
    result = validate_pure_state(state)
    assert result.is_valid_state
    assert result.state_norm_error < 1e-12


def test_pure_state_validation_flags_non_normalized_state() -> None:
    state = np.array([1.0, 1.0], dtype=complex)
    result = validate_pure_state(state)
    assert not result.is_valid_state
    assert result.state_norm_error > 1e-12


def test_estimate_error_bounds_accepts_branch_like_objects() -> None:
    rho = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    bounds = estimate_error_bounds([_BranchLike(rho)])
    assert bounds["machine_epsilon"] > 0.0
    assert bounds["spectral_perturbation_bound"] > 0.0


def test_canonicalize_near_zero_stabilizes_semantically_zero_values() -> None:
    assert canonicalize_near_zero(-3.749399456654645e-33) == 0.0
    assert canonicalize_near_zero(1e-12) == 1e-12
