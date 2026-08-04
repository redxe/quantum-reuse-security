"""State-preparation helpers for fixed-input BB84 analysis."""

import numpy as np

from .circuits import apply_single, ry, rz


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


__all__ = ["bb84_angles", "expected_victim_state", "prepare_advanced_state"]
