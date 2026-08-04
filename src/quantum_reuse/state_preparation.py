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


def prepare_parametric_state(theta: float, phi: float) -> np.ndarray:
    """Prepare the five-wire state for an arbitrary (theta, phi) signal-wire input.

    Equivalent to :func:`prepare_advanced_state` but bypasses the BB84 angle
    lookup.  ``q0`` and ``q1`` are initialised to ``|0>``; ``q2`` and ``q3``
    are prepared in ``Rz(phi) Ry(theta) |0>``.

    Args:
        theta: Ry rotation angle in radians.
        phi: Rz rotation angle in radians.

    Returns:
        Five-qubit state vector of shape ``(32,)``.
    """
    n = 5
    state = np.zeros(2**n, dtype=complex)
    state[0] = 1.0
    prep = rz(phi) @ ry(theta)
    state = apply_single(state, prep, 2, n)
    state = apply_single(state, prep, 3, n)
    return state


def expected_victim_state_parametric(theta: float, phi: float) -> np.ndarray:
    """Expected 4-qubit victim subsystem state for an arbitrary (theta, phi) input.

    After the two routing SWAPs, the victim subsystem ``q0..q3`` holds::

        |0, 0>  x  Rz(phi) Ry(theta) |0>  x  |0>

    (``q0``, ``q1`` are ``|0>`` because :func:`prepare_parametric_state` sets
    them to zero; ``q2`` receives the encoded duplicate; ``q3`` is the former
    workspace qubit.)

    Args:
        theta: Ry rotation angle in radians.
        phi: Rz rotation angle in radians.

    Returns:
        Four-qubit state vector of shape ``(16,)``.
    """
    n = 4
    state = np.zeros(2**n, dtype=complex)
    state[0] = 1.0
    prep = rz(phi) @ ry(theta)
    state = apply_single(state, prep, 2, n)
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


__all__ = [
    "bb84_angles",
    "expected_victim_state",
    "expected_victim_state_parametric",
    "prepare_advanced_state",
    "prepare_parametric_state",
]
