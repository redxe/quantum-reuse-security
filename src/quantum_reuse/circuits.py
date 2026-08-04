"""Circuit-level helpers and coherent-cleanup constructions."""

import numpy as np

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


def apply_single(state: np.ndarray, gate: np.ndarray, qubit: int, n: int) -> np.ndarray:
    tensor = state.reshape([2] * n)
    transformed = np.tensordot(gate, tensor, axes=([1], [qubit]))
    transformed = np.moveaxis(transformed, 0, qubit)
    return transformed.reshape(-1)


def apply_swap(state: np.ndarray, q1: int, q2: int, n: int) -> np.ndarray:
    tensor = state.reshape([2] * n)
    return np.swapaxes(tensor, q1, q2).reshape(-1)


def _apply_cnot(state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
    out = np.zeros_like(state)
    for i, amp in enumerate(state):
        bits = [((i >> (n - 1 - q)) & 1) for q in range(n)]
        if bits[control] == 1:
            bits[target] ^= 1
        j = 0
        for q, bit in enumerate(bits):
            j |= bit << (n - 1 - q)
        out[j] += amp
    return out


def _apply_cz(state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
    out = state.copy()
    for i in range(len(state)):
        control_bit = (i >> (n - 1 - control)) & 1
        target_bit = (i >> (n - 1 - target)) & 1
        if control_bit == 1 and target_bit == 1:
            out[i] *= -1
    return out


def swap_state_transfer_reference(psi: np.ndarray) -> np.ndarray:
    """
    SWAP-only state-transfer reference on three qubits.

    It applies SWAP(0,1) then SWAP(1,2), mapping |psi,0,0> -> |0,0,psi|.
    This preserves coherence and entanglement with external references.
    """
    n = 3
    state = np.zeros(2**n, dtype=complex)
    state[0] = psi[0]
    state[4] = psi[1]
    state = apply_swap(state, 0, 1, n)
    state = apply_swap(state, 1, 2, n)
    return state


def coherent_teleportation_cleanup_quirk(psi: np.ndarray) -> np.ndarray:
    """
    Exact Quirk-sequence coherent cleanup map on |psi,0,0>.

    Sequence:
        1) Bell preparation on (A,B): H(A), CNOT(A->B)
        2) Bell-basis interaction on (S,A): CNOT(S->A), H(S)
        3) Coherent corrections on B: CNOT(A->B), CZ(S->B)
        4) Final cleanup Hadamards: H(S), H(A)

    Qubit order is (S,A,B) = (0,1,2). For inputs |psi,0,0>, the result is
    exactly |0,0,psi> up to floating-point precision.
    """
    n = 3
    state = np.zeros(2**n, dtype=complex)
    state[0] = psi[0]
    state[4] = psi[1]

    state = apply_single(state, H, 1, n)
    state = _apply_cnot(state, 1, 2, n)
    state = _apply_cnot(state, 0, 1, n)
    state = apply_single(state, H, 0, n)
    state = _apply_cnot(state, 1, 2, n)
    state = _apply_cz(state, 0, 2, n)
    state = apply_single(state, H, 0, n)
    state = apply_single(state, H, 1, n)
    return state


def alternate_coherent_cleanup(psi: np.ndarray) -> np.ndarray:
    """
    Alternate coherent cleanup with coherent syndrome uncomputation.

    This variant maps |psi,0,0> to |0,0,psi> on the tested subspace and is
    retained for comparison against the exact Quirk-sequence implementation.
    """
    n = 3
    state = np.zeros(2**n, dtype=complex)
    state[0] = psi[0]
    state[4] = psi[1]

    state = apply_single(state, H, 1, n)
    state = _apply_cnot(state, 1, 2, n)
    state = _apply_cnot(state, 0, 1, n)
    state = apply_single(state, H, 0, n)
    state = _apply_cz(state, 0, 2, n)
    state = _apply_cnot(state, 1, 2, n)
    state = apply_single(state, H, 1, n)
    state = _apply_cnot(state, 0, 1, n)
    state = apply_single(state, H, 0, n)
    return state


def coherent_teleportation_cleanup_state(psi: np.ndarray) -> np.ndarray:
    """Backward-compatible alias for exact Quirk coherent cleanup."""
    return coherent_teleportation_cleanup_quirk(psi)


def coherent_cleanup_reference_state(psi: np.ndarray) -> np.ndarray:
    """Backward-compatible alias for the SWAP-only reference transfer."""
    return swap_state_transfer_reference(psi)


__all__ = [
    "H",
    "I2",
    "X",
    "apply_single",
    "apply_swap",
    "alternate_coherent_cleanup",
    "coherent_teleportation_cleanup_quirk",
    "coherent_teleportation_cleanup_state",
    "coherent_cleanup_reference_state",
    "swap_state_transfer_reference",
    "rz",
    "ry",
]
