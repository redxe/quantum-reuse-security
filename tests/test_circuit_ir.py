"""Issue #24 tests for liveness-aware circuit-IR payload injection."""

from __future__ import annotations

import numpy as np
import pytest

from quantum_reuse.circuit_ir import (
    Circuit,
    CircuitOperation,
    identify_reclaimed_qubits,
    inject_payload,
)
from quantum_reuse.circuits import apply_cnot
from quantum_reuse.compiler_pass import build_bb84_circuit
from quantum_reuse.measurements import reduced_density_pure
from quantum_reuse.metrics import trace_distance
from quantum_reuse.state_preparation import prepare_advanced_state

_N = 5
_Q_SIGNAL = 2
_Q_BOB = 3
_TOL = 1e-10


@pytest.mark.parametrize("value,basis", [(v, b) for v in (0, 1) for b in (0, 1)])
def test_bb84_ir_execution_matches_existing_state_preparation(value, basis) -> None:
    """The IR executes the same honest statevector as the Issue #14 model."""
    ir_state = build_bb84_circuit(value, basis).execute()
    reference_state = prepare_advanced_state(value, basis)
    assert np.allclose(ir_state, reference_state, atol=_TOL, rtol=0.0)


def test_identify_reclaimed_qubits_tracks_future_gate_uses() -> None:
    """Liveness returns every qubit with no later operation."""
    circuit = Circuit(
        3,
        (
            CircuitOperation("h", (0,)),
            CircuitOperation("cnot", (0, 1)),
            CircuitOperation("x", (2,)),
        ),
        protected_qubits=frozenset({0}),
    )

    assert identify_reclaimed_qubits(circuit, 0) == set()
    assert identify_reclaimed_qubits(circuit, 1) == {0, 1}
    assert identify_reclaimed_qubits(circuit, 2) == {0, 1, 2}


def test_payload_pass_selects_reclaimed_workspace_from_liveness() -> None:
    """The BB84 pass discovers q4 rather than receiving a target index."""
    honest = build_bb84_circuit(value=1, basis=0)
    injection_timestep = honest.last_use(_Q_SIGNAL)
    assert injection_timestep is not None
    assert identify_reclaimed_qubits(honest, injection_timestep) == {0, 1, 2, 4}

    injected = inject_payload(honest, _Q_SIGNAL)
    payload = injected.operations[injection_timestep + 1]
    assert payload.kind == "cnot"
    assert payload.qubits == (_Q_SIGNAL, 4)
    assert len(injected.operations) == len(honest.operations) + 1
    assert honest.operations[-1].kind == "rz"
    assert honest.operations[-1].qubits == (_Q_BOB,)


def test_payload_pass_uses_liveness_instead_of_protocol_index() -> None:
    """A generic IR selects its eligible dead wire, not the BB84 q4 position."""
    circuit = Circuit(
        4,
        (CircuitOperation("h", (0,)), CircuitOperation("x", (2,))),
        protected_qubits=frozenset({0, 3}),
    )

    injected = inject_payload(circuit, signal_qubit=0)
    assert injected.operations[1].kind == "cnot"
    assert injected.operations[1].qubits == (0, 1)


def test_payload_pass_rejects_circuits_without_reclaimed_workspace() -> None:
    """The pass refuses to overwrite a protected output when no target is live."""
    circuit = Circuit(
        2,
        (CircuitOperation("h", (0,)), CircuitOperation("h", (1,))),
        protected_qubits=frozenset({0, 1}),
    )

    with pytest.raises(ValueError, match="no unprotected reclaimed qubit"):
        inject_payload(circuit, signal_qubit=0)


def test_ir_injection_reproduces_bb84_victim_preservation_and_retention() -> None:
    """IR statevectors reproduce Issue #14's Z-basis victim and ancilla result."""
    ancilla_states = []
    for value in (0, 1):
        honest_circuit = build_bb84_circuit(value=value, basis=0)
        injection_timestep = honest_circuit.last_use(_Q_SIGNAL)
        assert injection_timestep is not None
        injected_circuit = inject_payload(honest_circuit, _Q_SIGNAL)
        ancilla_qubit = injected_circuit.operations[injection_timestep + 1].qubits[1]

        honest_state = honest_circuit.execute()
        injected_state = injected_circuit.execute()
        expected_injected = apply_cnot(
            prepare_advanced_state(value, 0), _Q_SIGNAL, ancilla_qubit, _N
        )
        assert np.allclose(injected_state, expected_injected, atol=_TOL, rtol=0.0)
        honest_victim = reduced_density_pure(honest_state, [_Q_BOB], _N)
        injected_victim = reduced_density_pure(injected_state, [_Q_BOB], _N)
        assert trace_distance(honest_victim, injected_victim) < _TOL

        ancilla_states.append(reduced_density_pure(injected_state, [ancilla_qubit], _N))

    assert trace_distance(ancilla_states[0], ancilla_states[1]) > 1 - _TOL
