import numpy as np

from quantum_reuse.circuits import H, X, apply_single, apply_swap, ry, rz
from quantum_reuse.measurements import measurement_branch, reduced_density_pure


def _basis_state(bits: tuple[int, ...]) -> np.ndarray:
    n = len(bits)
    index = 0
    for q, bit in enumerate(bits):
        index |= bit << (n - 1 - q)
    state = np.zeros(2**n, dtype=complex)
    state[index] = 1.0
    return state


def test_core_gates_are_unitary() -> None:
    eye = np.eye(2, dtype=complex)
    assert np.allclose(H.conj().T @ H, eye, atol=1e-12)
    assert np.allclose(X.conj().T @ X, eye, atol=1e-12)
    for theta in (0.0, np.pi / 7, np.pi / 2, np.pi):
        gate = ry(theta)
        assert np.allclose(gate.conj().T @ gate, eye, atol=1e-12)
    for phi in (0.0, np.pi / 5, np.pi / 2, np.pi):
        gate = rz(phi)
        assert np.allclose(gate.conj().T @ gate, eye, atol=1e-12)


def test_apply_single_x_maps_labeled_basis_states() -> None:
    state = _basis_state((0, 1, 0))
    out_q0 = apply_single(state, X, 0, 3)
    out_q2 = apply_single(state, X, 2, 3)
    assert np.allclose(out_q0, _basis_state((1, 1, 0)), atol=1e-12)
    assert np.allclose(out_q2, _basis_state((0, 1, 1)), atol=1e-12)


def test_apply_swap_preserves_norm_and_swaps_amplitudes() -> None:
    state = np.zeros(8, dtype=complex)
    state[1] = 0.3 + 0.4j  # |001>
    state[6] = -0.2 + 0.1j  # |110>
    swapped = apply_swap(state, 0, 2, 3)

    expected = np.zeros(8, dtype=complex)
    expected[4] = 0.3 + 0.4j  # |100>
    expected[3] = -0.2 + 0.1j  # |011>

    assert np.isclose(np.linalg.norm(swapped), np.linalg.norm(state), atol=1e-12)
    assert np.allclose(swapped, expected, atol=1e-12)


def test_measurement_branch_probabilities_sum_to_one_and_normalize() -> None:
    state = np.array([1, 2j, -1j, 0.5], dtype=complex)
    state = state / np.linalg.norm(state)
    p0, branch0 = measurement_branch(state, 0, 0, 2)
    p1, branch1 = measurement_branch(state, 0, 1, 2)
    assert np.isclose(p0 + p1, 1.0, atol=1e-12)
    if p0 > 1e-15:
        assert np.isclose(np.vdot(branch0, branch0).real, 1.0, atol=1e-12)
    if p1 > 1e-15:
        assert np.isclose(np.vdot(branch1, branch1).real, 1.0, atol=1e-12)


def test_reduced_density_is_trace_one_and_hermitian() -> None:
    state = np.array([1, 1j, -1, 2], dtype=complex)
    state = state / np.linalg.norm(state)
    rho = reduced_density_pure(state, [0], 2)
    assert np.isclose(np.trace(rho).real, 1.0, atol=1e-12)
    assert np.allclose(rho, rho.conj().T, atol=1e-12)


def test_bell_partial_trace_is_maximally_mixed() -> None:
    bell = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    rho0 = reduced_density_pure(bell, [0], 2)
    rho1 = reduced_density_pure(bell, [1], 2)
    target = 0.5 * np.eye(2, dtype=complex)
    assert np.allclose(rho0, target, atol=1e-12)
    assert np.allclose(rho1, target, atol=1e-12)
