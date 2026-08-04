import numpy as np

from quantum_reuse.metrics import (
    binary_entropy,
    bloch_vector,
    fidelity_with_pure,
    trace_distance,
)


def test_trace_distance_vanishes_for_identical_states() -> None:
    rho = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    assert np.isclose(trace_distance(rho, rho), 0.0, atol=1e-12)


def test_trace_distance_for_orthogonal_pure_states_is_one() -> None:
    ket0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    ket1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    assert np.isclose(trace_distance(ket0, ket1), 1.0, atol=1e-12)


def test_fidelity_with_pure_state_one_for_matching_projector() -> None:
    rho = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    pure = np.array([1.0, 0.0], dtype=complex)
    assert np.isclose(fidelity_with_pure(rho, pure), 1.0, atol=1e-12)


def test_bloch_vector_for_basis_states_and_maximally_mixed_state() -> None:
    ket0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    maximally_mixed = 0.5 * np.eye(2, dtype=complex)
    assert np.allclose(bloch_vector(ket0), (0.0, 0.0, 1.0), atol=1e-12)
    assert np.allclose(bloch_vector(maximally_mixed), (0.0, 0.0, 0.0), atol=1e-12)


def test_binary_entropy_boundary_values_and_midpoint() -> None:
    assert np.isclose(binary_entropy(0.5), 1.0, atol=1e-12)
    assert np.isclose(binary_entropy(0.0), 0.0, atol=1e-12)
