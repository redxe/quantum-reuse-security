import numpy as np

from quantum_reuse.circuits import (
    coherent_teleportation_cleanup_state,
    swap_state_transfer_reference,
)


def _state(amp0: complex, amp1: complex) -> np.ndarray:
    psi = np.array([amp0, amp1], dtype=complex)
    return psi / np.linalg.norm(psi)


def test_coherent_cleanup_identity() -> None:
    psi = _state(1 + 0j, 1j)
    out = coherent_teleportation_cleanup_state(psi)
    expected = np.zeros(8, dtype=complex)
    expected[0] = psi[0]
    expected[1] = psi[1]
    assert np.allclose(out, expected, atol=1e-12)


def test_swap_state_transfer_reference_identity() -> None:
    psi = _state(0.3 + 0.4j, -0.2 + 0.8j)
    out = swap_state_transfer_reference(psi)
    expected = np.zeros(8, dtype=complex)
    expected[0] = psi[0]
    expected[1] = psi[1]
    assert np.allclose(out, expected, atol=1e-12)


def test_entangled_reference_preservation() -> None:
    # Build Bell pair between reference R and system S, append ancillas |00>.
    bell = np.zeros(16, dtype=complex)
    bell[0] = 1 / np.sqrt(2)  # |0_R 0_S 0 0>
    bell[12] = 1 / np.sqrt(2)  # |1_R 1_S 0 0>

    reshaped = bell.reshape(2, 2, 2, 2)

    # Apply coherent cleanup on (S, A, B) = qubits (1,2,3).
    out = np.zeros_like(bell)
    for r in (0, 1):
        psi = reshaped[r, :, 0, 0]
        moved = coherent_teleportation_cleanup_state(psi)
        out[r * 8 : (r + 1) * 8] = moved

    out_tensor = out.reshape(2, 2, 2, 2)
    # Check perfect correlations moved from (R,S) to (R,B).
    # R and B should be Bell-correlated with A,S in |00>.
    assert np.allclose(
        out_tensor[:, 0, 0, :],
        np.array([[1 / np.sqrt(2), 0], [0, 1 / np.sqrt(2)]], dtype=complex),
        atol=1e-12,
    )


def test_swap_and_coherent_cleanup_match_on_restricted_subspace() -> None:
    psi = _state(np.sqrt(0.31), np.sqrt(0.69) * np.exp(1j * 0.37))
    swap_out = swap_state_transfer_reference(psi)
    coherent_out = coherent_teleportation_cleanup_state(psi)
    assert np.allclose(swap_out, coherent_out, atol=1e-12)
