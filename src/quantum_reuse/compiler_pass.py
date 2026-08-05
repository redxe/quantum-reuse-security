"""Liveness-aware malicious injection transformation (Issue #24).

Demonstrates that a privileged agent with **use** access to the qubit register
can achieve **retain** by inserting a CNOT coupling from a secret-carrying
signal wire into an idle workspace qubit, while leaving the victim's observable
output unchanged.

The transformation operates on a minimal executable circuit IR.  It uses
liveness analysis to discover an unprotected qubit with no future gates after
Alice's signal preparation, then inserts a CNOT payload at that point.  The
five-wire example still identifies q4 as the available workspace, but the pass
never selects q4 by a hard-coded target index.  See ``docs/THREAT_MODEL.md``
§7 for the distinction between this constructive demonstration and the open
formal bound.

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

from .circuit_ir import (
    Circuit,
    CircuitOperation,
    identify_reclaimed_qubits,
    inject_payload,
)
from .measurements import reduced_density_pure
from .metrics import fidelity_with_pure, trace_distance
from .state_preparation import bb84_angles

# ── System constants ────────────────────────────────────────────────────────
_N = 5  # Total qubits
_Q_VALUE = 0  # Alice's value selector
_Q_BASIS = 1  # Alice's basis selector
_Q_SIGNAL = 2  # Alice's signal wire (injection source)
_Q_BOB = 3  # Bob's copy (victim output)

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


# ── Circuit construction and IR execution ──────────────────────────────────


def _signal_preparation_operations(theta: float, phi: float) -> list[CircuitOperation]:
    """Return the matched q2/q3 preparation gates used by the five-wire model."""
    return [
        CircuitOperation("ry", (_Q_SIGNAL,), theta),
        CircuitOperation("rz", (_Q_SIGNAL,), phi),
        CircuitOperation("ry", (_Q_BOB,), theta),
        CircuitOperation("rz", (_Q_BOB,), phi),
    ]


def _protected_protocol_qubits() -> frozenset[int]:
    """Return wires whose completed state remains user-visible or secret-bearing."""
    return frozenset({_Q_VALUE, _Q_BASIS, _Q_SIGNAL, _Q_BOB})


def build_bb84_circuit(value: int, basis: int) -> Circuit:
    """Build the honest five-wire BB84 preparation as executable IR.

    The returned circuit leaves the fifth wire unprotected and untouched.  Its
    lifetime is therefore discovered by :func:`identify_reclaimed_qubits`, not
    encoded into the injection transformation.
    """
    if value not in (0, 1) or basis not in (0, 1):
        raise ValueError("value and basis must each be 0 or 1")

    theta, phi = bb84_angles(value, basis)
    operations: list[CircuitOperation] = []
    if value:
        operations.append(CircuitOperation("x", (_Q_VALUE,)))
    if basis:
        operations.append(CircuitOperation("x", (_Q_BASIS,)))
    operations.extend(_signal_preparation_operations(theta, phi))
    return Circuit(_N, tuple(operations), _protected_protocol_qubits())


def build_parametric_circuit(theta: float, phi: float) -> Circuit:
    """Build the honest five-wire arbitrary-state preparation as executable IR."""
    return Circuit(
        _N,
        tuple(_signal_preparation_operations(theta, phi)),
        _protected_protocol_qubits(),
    )


def _statevectors_after_ir_injection(
    circuit: Circuit,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Execute honest and transformed IR statevectors and return payload target."""
    injection_timestep = circuit.last_use(_Q_SIGNAL)
    if injection_timestep is None:
        raise RuntimeError("five-wire circuit is missing signal preparation")

    injected_circuit = inject_payload(circuit, _Q_SIGNAL, injection_timestep)
    payload = injected_circuit.operations[injection_timestep + 1]
    if payload.kind != "cnot" or payload.qubits[0] != _Q_SIGNAL:
        raise RuntimeError("payload pass did not insert the expected signal coupling")
    return circuit.execute(), injected_circuit.execute(), payload.qubits[1]


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

    honest_circuit = build_bb84_circuit(value, basis)
    honest, injected, ancilla_qubit = _statevectors_after_ir_injection(honest_circuit)

    victim_honest = reduced_density_pure(honest, [_Q_BOB], _N)
    victim_injected = reduced_density_pure(injected, [_Q_BOB], _N)

    fid_honest = fidelity_with_pure(victim_honest, target)
    fid_injected = fidelity_with_pure(victim_injected, target)
    victim_td = trace_distance(victim_honest, victim_injected)
    victim_preserved = victim_td < _PRESERVATION_TOL

    ancilla_honest = reduced_density_pure(honest, [ancilla_qubit], _N)
    ancilla_injected = reduced_density_pure(injected, [ancilla_qubit], _N)

    # Attacker advantage: TD between ancilla for v=0 and v=1 at same basis
    _, injected_v0, ancilla_v0_qubit = _statevectors_after_ir_injection(
        build_bb84_circuit(0, basis)
    )
    _, injected_v1, ancilla_v1_qubit = _statevectors_after_ir_injection(
        build_bb84_circuit(1, basis)
    )
    anc_v0 = reduced_density_pure(injected_v0, [ancilla_v0_qubit], _N)
    anc_v1 = reduced_density_pure(injected_v1, [ancilla_v1_qubit], _N)
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

    honest_circuit = build_parametric_circuit(theta, phi)
    honest, injected, ancilla_qubit = _statevectors_after_ir_injection(honest_circuit)

    victim_honest = reduced_density_pure(honest, [_Q_BOB], _N)
    victim_injected = reduced_density_pure(injected, [_Q_BOB], _N)

    fid_injected = fidelity_with_pure(victim_injected, target)
    victim_td = trace_distance(victim_honest, victim_injected)
    victim_preserved = victim_td < _PRESERVATION_TOL

    ancilla_injected = reduced_density_pure(injected, [ancilla_qubit], _N)
    zero_rho = np.array([[1, 0], [0, 0]], dtype=complex)
    att_td_to_zero = trace_distance(ancilla_injected, zero_rho)

    return victim_preserved, fid_injected, att_td_to_zero


__all__ = [
    "Circuit",
    "CircuitOperation",
    "InjectionAnalysis",
    "analyze_injection",
    "analyze_injection_parametric",
    "build_bb84_circuit",
    "build_parametric_circuit",
    "identify_reclaimed_qubits",
    "inject_payload",
]
