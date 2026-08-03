import numpy as np

from quantum_reuse.state_preparation import bb84_angles
from quantum_reuse.validation import validate_density_matrix, validate_pure_state
from quantum_reuse.parameterized_fifth_wire_analysis import rz, ry


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


def test_pure_state_validation() -> None:
    state = np.array([1.0, 0.0], dtype=complex)
    result = validate_pure_state(state)
    assert result.is_valid_state
    assert result.state_norm_error < 1e-12
