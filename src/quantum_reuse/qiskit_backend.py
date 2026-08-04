"""Qiskit-backed circuit path for the five-wire spy protocol.

Provides :func:`enumerate_eve_branches_qiskit` which replicates the
deterministic NumPy branch model using Qiskit Statevector simulation
within explicit numerical tolerances.  Requires qiskit>=1.0.0::

    pip install 'quantum-reuse-security[qiskit]'

When qiskit is not installed the module is still importable.  Functions
that need it raise :class:`ImportError` at call time.  Use
:func:`qiskit_available` to probe availability before calling them.

Qubit mapping
-------------
Qiskit uses little-endian bit ordering (q[0] = LSB).  We map each NumPy
qubit k to Qiskit q[n-1-k] (n=5).  This reversal preserves statevector
index parity between the two models, so ``Statevector(circuit).data``
has the same index convention as our NumPy state vectors::

    q[4] = numpy q0  (Alice value selector)
    q[3] = numpy q1  (Alice basis selector)
    q[2] = numpy q2  (signal / Eve-measurement wire)
    q[1] = numpy q3  (Bob duplicate wire)
    q[0] = numpy q4  (workspace / fifth wire)
"""

from __future__ import annotations

import numpy as np

_QISKIT_AVAILABLE: bool = False
try:
    from qiskit import QuantumCircuit as _QC  # noqa: F401
    from qiskit.quantum_info import (  # noqa: F401
        Statevector as _SV,
        partial_trace as _pt,
    )

    _QISKIT_AVAILABLE = True
except ImportError:
    pass

# Qiskit qubit indices (little-endian)
_Q_VALUE: int = 4  # Alice value
_Q_BASIS: int = 3  # Alice basis
_Q_EVE: int = 2  # Eve / signal wire
_Q_BOB: int = 1  # Bob duplicate
_Q_FIFTH: int = 0  # workspace / fifth wire


def qiskit_available() -> bool:
    """Return True if qiskit is importable in the current environment."""
    return _QISKIT_AVAILABLE


def _require_qiskit() -> None:
    if not _QISKIT_AVAILABLE:
        raise ImportError(
            "qiskit is required for this function. "
            "Install with: pip install 'quantum-reuse-security[qiskit]'"
        )


def build_protocol_circuit(value: int, basis: int, eve_basis: int):
    """Build the five-wire spy protocol QuantumCircuit.

    The returned circuit ends just before Eve's measurement.  Simulate
    with ``Statevector(circuit)`` to obtain the pre-measurement state.
    The resulting statevector array shares its index convention with the
    NumPy model.

    Args:
        value: Alice's encoded bit (0 or 1).
        basis: Alice's basis choice (0=Z, 1=X).
        eve_basis: Eve's measurement basis (0=Z, 1=X).

    Returns:
        A 5-qubit :class:`~qiskit.QuantumCircuit`.

    Raises:
        ImportError: if qiskit is not installed.
    """
    _require_qiskit()
    from qiskit import QuantumCircuit

    from .state_preparation import bb84_angles

    theta, phi = bb84_angles(value, basis)
    qc = QuantumCircuit(5, name=f"spy_v{value}_b{basis}_e{eve_basis}")

    if value:
        qc.x(_Q_VALUE)
    if basis:
        qc.x(_Q_BASIS)

    # Alice prepares the signal wire and Bob's duplicate
    qc.ry(theta, _Q_EVE)
    qc.rz(phi, _Q_EVE)
    qc.ry(theta, _Q_BOB)
    qc.rz(phi, _Q_BOB)

    # Eve's optional basis rotation before measurement
    if eve_basis == 1:
        qc.h(_Q_EVE)

    return qc


def _project(
    sv_data: np.ndarray, qubit_lsb: int, outcome: int
) -> tuple[float, np.ndarray]:
    """Project a little-endian statevector onto one qubit outcome.

    Args:
        sv_data: 1-D complex numpy array (Qiskit little-endian convention).
        qubit_lsb: Qiskit qubit index (0 = LSB).
        outcome: Measurement outcome (0 or 1).

    Returns:
        ``(probability, normalised_projected_state)``
    """
    indices = np.arange(len(sv_data))
    keep = ((indices >> qubit_lsb) & 1) == outcome
    projected = sv_data * keep
    prob = float(np.real(np.vdot(projected, projected)))
    if prob > 1e-15:
        projected = projected / np.sqrt(prob)
    return prob, projected


def enumerate_eve_branches_qiskit(value: int, basis: int, eve_basis: int) -> list:
    """Replicate enumerate_eve_branches() via Qiskit Statevector simulation.

    Returns a list of :class:`~quantum_reuse.measurements.BranchResult`
    with the same schema as the NumPy model.  Branch probabilities,
    fifth-wire density matrices, and victim-subsystem density matrices
    agree with the NumPy reference within 1e-12.

    The qubit mapping and index-parity argument are documented in this
    module's docstring.

    Args:
        value: Alice's encoded bit (0 or 1).
        basis: Alice's basis choice (0=Z, 1=X).
        eve_basis: Eve's measurement basis (0=Z, 1=X).

    Returns:
        List of :class:`~quantum_reuse.measurements.BranchResult`, one
        per non-negligible Eve measurement outcome.

    Raises:
        ImportError: if qiskit is not installed.
    """
    _require_qiskit()
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector, partial_trace

    from .measurements import BranchResult
    from .metrics import fidelity_with_pure, trace_distance
    from .state_preparation import expected_victim_state

    pre_meas_sv = Statevector(build_protocol_circuit(value, basis, eve_basis)).data

    target_victim = expected_victim_state(value, basis)
    target_victim_rho = np.outer(target_victim, target_victim.conj())

    # Routing circuit mirrors the NumPy model's two SWAPs:
    #   numpy SWAP(q3, q4) -> Qiskit swap(_Q_BOB,  _Q_FIFTH)
    #   numpy SWAP(q2, q4) -> Qiskit swap(_Q_EVE,  _Q_FIFTH)
    routing_qc = QuantumCircuit(5, name="routing")
    routing_qc.swap(_Q_BOB, _Q_FIFTH)
    routing_qc.swap(_Q_EVE, _Q_FIFTH)

    results: list[BranchResult] = []
    for eve_result in (0, 1):
        prob, branch_data = _project(pre_meas_sv, _Q_EVE, eve_result)
        if prob < 1e-14:
            continue

        routed_sv = Statevector(branch_data).evolve(routing_qc)

        # fifth wire = q[0]; trace out all others
        fifth_rho = partial_trace(routed_sv, [1, 2, 3, 4]).data
        # victim = q[1..4]; trace out q[0]
        victim_rho = partial_trace(routed_sv, [0]).data

        results.append(
            BranchResult(
                value=value,
                basis=basis,
                eve_basis=eve_basis,
                eve_result=eve_result,
                branch_probability=prob,
                fifth_rho=fifth_rho,
                victim_rho=victim_rho,
                victim_fidelity=fidelity_with_pure(victim_rho, target_victim),
                victim_trace_distance=trace_distance(victim_rho, target_victim_rho),
            )
        )

    return results


__all__ = [
    "build_protocol_circuit",
    "enumerate_eve_branches_qiskit",
    "qiskit_available",
]
