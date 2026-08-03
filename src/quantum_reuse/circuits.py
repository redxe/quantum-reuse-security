"""Circuit-level helpers and coherent cleanup reference construction."""

import numpy as np

from .parameterized_fifth_wire_analysis import H, I2, X, apply_single, apply_swap, rz, ry


def coherent_cleanup_reference_state(psi: np.ndarray) -> np.ndarray:
    """
    Reference coherent cleanup map on three qubits.

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


__all__ = [
    "H",
    "I2",
    "X",
    "apply_single",
    "apply_swap",
    "coherent_cleanup_reference_state",
    "rz",
    "ry",
]
