"""Proof-of-concept malicious injection transformation (Issue #14).

Demonstrates that a privileged agent with **use** access to the qubit register
can achieve **retain** by inserting a CNOT coupling from a secret-carrying
signal wire into an idle workspace qubit, while leaving the victim's observable
output unchanged.

This is a hard-coded statevector transformation on the five-wire NumPy model.
It does not yet include an intermediate representation, liveness analysis,
reclaimed-qubit discovery, or pass scheduling.  Those components belong in the
next milestone (full liveness-aware circuit transformation).  See
``docs/THREAT_MODEL.md`` §7 for the distinction between this constructive
demonstration and the open formal bound.

Qubit layout (big-endian, q0 = MSB)::

    q0  Alice's value selector (classical bit, initialised from *value*)
    q1  Alice's basis selector (classical bit, initialised from *basis*)
    q2  Alice's signal wire — the injection *source*
    q3  Bob's duplicate signal wire — the *victim* observable
    q4  Idle workspace qubit — the injection *target* (ancilla)

Injection point
---------------
The malicious CNOT(q2 → q4) is inserted after Alice's signal preparation and
before any routing or measurement.  Because q3 is a structurally separate wire,
q3 preservation is guaranteed by disjointness.  The honest-vs-injected
equivalence is verified explicitly via trace distance rather than relying on
this structural argument.

Key results
-----------
- Victim (q3) trace distance between honest and injected states is 0 for all
  tested inputs.  ``victim_preserved`` uses this direct state comparison as the
  equivalence criterion; target fidelities are kept as supporting diagnostics.
- Z-basis: injected ancilla = ``|v><v|``; attacker trace distance between
  v=0 and v=1 ancilla states = 1 (perfect retain of Alice's value).
  Label: ``use -> retain(v); export not modeled``.
- X-basis: injected ancilla = ``I/2``; attacker trace distance = 0.
  The ancilla carries no value information without Alice's basis.
  Label: ``use only; no retain(v)``.
- Export privilege is not present in this prototype: no output channel for q4
  exists.  The Z-basis result shows q4 *could* be exported, but that step
  is not modelled here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .circuits import apply_cnot
from .measurements import reduced_density_pure
from .metrics import fidelity_with_pure, trace_distance
from .state_preparation import (
    bb84_angles,
    prepare_advanced_state,
    prepare_parametric_state,
)

# ── System constants ────────────────────────────────────────────────────────
_N = 5  # Total qubits
_Q_VALUE = 0  # Alice's value selector
_Q_BASIS = 1  # Alice's basis selector
_Q_SIGNAL = 2  # Alice's signal wire (injection source)
_Q_BOB = 3  # Bob's copy (victim output)
_Q_ANCILLA = 4  # Reclaimed workspace (injection target)

_PRESERVATION_TOL = 1e-10

# ── Data classes ────────────────────────────────────────────────────────────


@dataclass
class InjectionAnalysis:
    """Comparison of honest and injected circuits for a single (value, basis).

    Attributes:
        value: Alice's bit value (0 or 1).
        basis: Alice's encoding basis (0 = Z, 1 = X).
        victim_trace_distance: Trace distance between the honest and injected
            victim reduced states.  Primary equivalence criterion for
            ``victim_preserved``.
        victim_fidelity_honest: Fidelity of Bob's reduced state with the
            expected pure state in the honest circuit.  Supporting diagnostic.
        victim_fidelity_injected: Same fidelity after injection.
            Supporting diagnostic.
        victim_preserved: True when ``victim_trace_distance < _PRESERVATION_TOL``.
        ancilla_rho_honest: 2×2 reduced density matrix of q4 in the honest
            circuit.  Equals |0><0| because q4 is never touched.
        ancilla_rho_injected: 2×2 reduced density matrix of q4 after the
            malicious CNOT.
        attacker_trace_distance: Trace distance between injected ancilla states
            for v=0 and v=1 at this basis.
        privilege_converted: Privilege label using use/read/retain/export
            vocabulary.
    """

    value: int
    basis: int
    victim_trace_distance: float
    victim_fidelity_honest: float
    victim_fidelity_injected: float
    victim_preserved: bool
    ancilla_rho_honest: np.ndarray
    ancilla_rho_injected: np.ndarray
    attacker_trace_distance: float
    privilege_converted: str


# ── Internal helpers ────────────────────────────────────────────────────────


def _honest_state(value: int, basis: int) -> np.ndarray:
    """Five-wire state after Alice's preparation, no injection."""
    return prepare_advanced_state(value, basis)


def _injected_state(value: int, basis: int) -> np.ndarray:
    """Five-wire state after Alice's preparation + CNOT(q2 → q4) injection."""
    return apply_cnot(prepare_advanced_state(value, basis), _Q_SIGNAL, _Q_ANCILLA, _N)


def _honest_state_parametric(theta: float, phi: float) -> np.ndarray:
    return prepare_parametric_state(theta, phi)


def _injected_state_parametric(theta: float, phi: float) -> np.ndarray:
    return apply_cnot(prepare_parametric_state(theta, phi), _Q_SIGNAL, _Q_ANCILLA, _N)


# ── Public API ───────────────────────────────────────────────────────────────


def analyze_injection(value: int, basis: int) -> InjectionAnalysis:
    """Analyse the effect of CNOT(q_signal → q_ancilla) for a BB84 input.

    Compares the honest circuit (no injection) against the injected circuit
    on two metrics:

    1. Victim preservation: does Bob's reduced state (q3) change?
    2. Attacker advantage: how well can the attacker distinguish v=0 from v=1
       by reading the ancilla?

    Args:
        value: Alice's bit value (0 or 1).
        basis: Alice's basis (0 = Z, 1 = X).

    Returns:
        :class:`InjectionAnalysis` for this (value, basis) pair.
    """
    theta, phi = bb84_angles(value, basis)
    target = np.zeros(2, dtype=complex)
    # q3's expected state is the single-qubit signal state
    target[0] = np.cos(theta / 2)
    target[1] = np.exp(1j * phi) * np.sin(theta / 2)

    honest = _honest_state(value, basis)
    injected = _injected_state(value, basis)

    victim_honest = reduced_density_pure(honest, [_Q_BOB], _N)
    victim_injected = reduced_density_pure(injected, [_Q_BOB], _N)

    fid_honest = fidelity_with_pure(victim_honest, target)
    fid_injected = fidelity_with_pure(victim_injected, target)
    victim_td = trace_distance(victim_honest, victim_injected)
    victim_preserved = victim_td < _PRESERVATION_TOL

    ancilla_honest = reduced_density_pure(honest, [_Q_ANCILLA], _N)
    ancilla_injected = reduced_density_pure(injected, [_Q_ANCILLA], _N)

    # Attacker advantage: TD between ancilla for v=0 and v=1 at same basis
    anc_v0 = reduced_density_pure(_injected_state(0, basis), [_Q_ANCILLA], _N)
    anc_v1 = reduced_density_pure(_injected_state(1, basis), [_Q_ANCILLA], _N)
    att_td = trace_distance(anc_v0, anc_v1)

    # Privilege label using use/read/retain/export vocabulary.
    # retain(v) requires the ancilla to carry distinguishable information about v.
    # export is not present in this prototype (no output channel for q4).
    if att_td > _PRESERVATION_TOL:
        priv = "use -> retain(v); export not modeled"
    else:
        priv = "use only; no retain(v)"

    return InjectionAnalysis(
        value=value,
        basis=basis,
        victim_trace_distance=victim_td,
        victim_fidelity_honest=fid_honest,
        victim_fidelity_injected=fid_injected,
        victim_preserved=victim_preserved,
        ancilla_rho_honest=ancilla_honest,
        ancilla_rho_injected=ancilla_injected,
        attacker_trace_distance=att_td,
        privilege_converted=priv,
    )


def analyze_injection_parametric(theta: float, phi: float) -> tuple[bool, float, float]:
    """Check victim preservation and attacker advantage for arbitrary (theta, phi).

    Evaluates CNOT(q_signal → q_ancilla) on the parametric five-wire state.

    Args:
        theta: Ry rotation angle for Alice's signal preparation (radians).
        phi: Rz rotation angle for Alice's signal preparation (radians).

    Returns:
        Tuple ``(victim_preserved, victim_fidelity_injected,
        attacker_trace_distance_to_zero)`` where:

        - ``victim_preserved`` is True when the CNOT does not disturb Bob's
          reduced state above the tolerance.
        - ``victim_fidelity_injected`` is the fidelity of Bob's reduced state
          with the expected signal state after injection.
        - ``attacker_trace_distance_to_zero`` is the trace distance between
          the injected ancilla state and |0><0|.  A non-zero value means the
          ancilla deviates from its initial state, indicating information
          retention.
    """
    target = np.zeros(2, dtype=complex)
    target[0] = np.cos(theta / 2)
    target[1] = np.exp(1j * phi) * np.sin(theta / 2)

    honest = _honest_state_parametric(theta, phi)
    injected = _injected_state_parametric(theta, phi)

    victim_honest = reduced_density_pure(honest, [_Q_BOB], _N)
    victim_injected = reduced_density_pure(injected, [_Q_BOB], _N)

    fid_injected = fidelity_with_pure(victim_injected, target)
    victim_td = trace_distance(victim_honest, victim_injected)
    victim_preserved = victim_td < _PRESERVATION_TOL

    ancilla_injected = reduced_density_pure(injected, [_Q_ANCILLA], _N)
    zero_rho = np.array([[1, 0], [0, 0]], dtype=complex)
    att_td_to_zero = trace_distance(ancilla_injected, zero_rho)

    return victim_preserved, fid_injected, att_td_to_zero


__all__ = [
    "InjectionAnalysis",
    "analyze_injection",
    "analyze_injection_parametric",
]
