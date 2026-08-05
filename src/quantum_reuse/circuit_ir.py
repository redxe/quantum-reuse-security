"""Minimal executable circuit IR and liveness-aware payload transformation.

The IR deliberately models only the unitary gates used by the current NumPy
five-wire prototype.  It is enough to make qubit lifetimes explicit, execute
the honest and transformed statevectors, and inject a CNOT payload into an
unprotected qubit whose lifetime has ended at the selected insertion point.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import FrozenSet, Optional, Set, Tuple

import numpy as np

from .circuits import H, X, apply_cnot, apply_single, apply_swap, ry, rz

_GATE_ARITY = {
    "h": 1,
    "x": 1,
    "ry": 1,
    "rz": 1,
    "cnot": 2,
    "swap": 2,
}
_PARAMETRIC_GATES = frozenset({"ry", "rz"})


@dataclass(frozen=True)
class CircuitOperation:
    """One unitary operation in a :class:`Circuit` gate list."""

    kind: str
    qubits: Tuple[int, ...]
    parameter: Optional[float] = None

    def __post_init__(self) -> None:
        qubits = tuple(self.qubits)
        object.__setattr__(self, "qubits", qubits)

        if self.kind not in _GATE_ARITY:
            raise ValueError(f"unsupported circuit operation: {self.kind}")
        if len(qubits) != _GATE_ARITY[self.kind]:
            raise ValueError(
                f"{self.kind} requires {_GATE_ARITY[self.kind]} qubits, "
                f"got {len(qubits)}"
            )
        if len(set(qubits)) != len(qubits):
            raise ValueError(f"{self.kind} cannot address the same qubit twice")
        if self.kind in _PARAMETRIC_GATES and self.parameter is None:
            raise ValueError(f"{self.kind} requires a rotation parameter")
        if self.kind not in _PARAMETRIC_GATES and self.parameter is not None:
            raise ValueError(f"{self.kind} does not accept a rotation parameter")


@dataclass(frozen=True)
class Circuit:
    """Ordered quantum gate list with protected user-visible qubits.

    ``protected_qubits`` remain externally observable or secret-bearing even
    after their final operation.  Liveness reports their expired lifetime;
    transformations use this metadata to avoid treating them as workspace.
    """

    n_qubits: int
    operations: Tuple[CircuitOperation, ...] = ()
    protected_qubits: FrozenSet[int] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.n_qubits <= 0:
            raise ValueError("a circuit must contain at least one qubit")

        operations = tuple(self.operations)
        protected_qubits = frozenset(self.protected_qubits)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "protected_qubits", protected_qubits)

        for operation in operations:
            if not isinstance(operation, CircuitOperation):
                raise TypeError("circuit operations must be CircuitOperation instances")
            for qubit in operation.qubits:
                self._validate_qubit(qubit)
        for qubit in protected_qubits:
            self._validate_qubit(qubit)

    def _validate_qubit(self, qubit: int) -> None:
        if not 0 <= qubit < self.n_qubits:
            raise ValueError(
                f"qubit q{qubit} is outside a {self.n_qubits}-qubit circuit"
            )

    def last_use(self, qubit: int) -> Optional[int]:
        """Return the final operation index touching ``qubit``, if any."""
        self._validate_qubit(qubit)
        for timestep in range(len(self.operations) - 1, -1, -1):
            if qubit in self.operations[timestep].qubits:
                return timestep
        return None

    def future_qubits_after(self, timestep: int) -> Set[int]:
        """Return qubits touched strictly after an operation index."""
        if timestep < -1 or timestep >= len(self.operations):
            raise ValueError(
                f"timestep {timestep} is outside the circuit operation range"
            )
        return {
            qubit
            for operation in self.operations[timestep + 1 :]
            for qubit in operation.qubits
        }

    def insert_after(self, timestep: int, operation: CircuitOperation) -> "Circuit":
        """Return a new circuit with ``operation`` inserted after ``timestep``."""
        if not isinstance(operation, CircuitOperation):
            raise TypeError("inserted operation must be a CircuitOperation")
        if timestep < -1 or timestep >= len(self.operations):
            raise ValueError(
                f"timestep {timestep} is outside the circuit operation range"
            )
        for qubit in operation.qubits:
            self._validate_qubit(qubit)
        return replace(
            self,
            operations=self.operations[: timestep + 1]
            + (operation,)
            + self.operations[timestep + 1 :],
        )

    def execute(self, initial_state: Optional[np.ndarray] = None) -> np.ndarray:
        """Execute the gate list using the project's big-endian NumPy backend."""
        if initial_state is None:
            state = np.zeros(2**self.n_qubits, dtype=complex)
            state[0] = 1.0
        else:
            state = np.asarray(initial_state, dtype=complex).copy()
            if state.ndim != 1 or state.size != 2**self.n_qubits:
                raise ValueError(
                    "initial state must be a vector of length " f"2**{self.n_qubits}"
                )

        for operation in self.operations:
            state = _apply_operation(state, operation, self.n_qubits)
        return state


def _apply_operation(
    state: np.ndarray, operation: CircuitOperation, n_qubits: int
) -> np.ndarray:
    if operation.kind == "h":
        return apply_single(state, H, operation.qubits[0], n_qubits)
    if operation.kind == "x":
        return apply_single(state, X, operation.qubits[0], n_qubits)
    if operation.kind == "ry":
        if operation.parameter is None:
            raise RuntimeError("validated ry operation has no parameter")
        return apply_single(
            state, ry(operation.parameter), operation.qubits[0], n_qubits
        )
    if operation.kind == "rz":
        if operation.parameter is None:
            raise RuntimeError("validated rz operation has no parameter")
        return apply_single(
            state, rz(operation.parameter), operation.qubits[0], n_qubits
        )
    if operation.kind == "cnot":
        return apply_cnot(state, operation.qubits[0], operation.qubits[1], n_qubits)
    if operation.kind == "swap":
        return apply_swap(state, operation.qubits[0], operation.qubits[1], n_qubits)
    raise RuntimeError(f"validated operation is not executable: {operation.kind}")


def identify_reclaimed_qubits(
    circuit: Circuit, timestep: Optional[int] = None
) -> Set[int]:
    """Return qubits with no future gates after ``timestep``.

    Operation indices are zero-based.  When ``timestep`` is omitted, the end
    of the circuit is used.  This is a liveness result, so it can include
    protected output wires; :func:`inject_payload` filters those separately
    before choosing an injection target.
    """
    if timestep is None:
        timestep = len(circuit.operations) - 1
    future_qubits = circuit.future_qubits_after(timestep)
    return set(range(circuit.n_qubits)) - future_qubits


def inject_payload(
    circuit: Circuit, signal_qubit: int, timestep: Optional[int] = None
) -> Circuit:
    """Insert a CNOT payload from ``signal_qubit`` to a reclaimed workspace.

    The target is selected from liveness candidates, never supplied as a
    hard-coded wire index.  The lowest eligible qubit is used so the pass is
    deterministic.  A circuit with no unprotected reclaimed target is
    rejected instead of silently modifying a protected output.  Callers must
    declare every externally observable or secret-bearing wire in
    ``Circuit.protected_qubits``; an unmarked dead wire is eligible workspace.
    """
    circuit._validate_qubit(signal_qubit)
    if timestep is None:
        timestep = circuit.last_use(signal_qubit)
        if timestep is None:
            raise ValueError("signal qubit must be prepared before payload injection")

    eligible_targets = identify_reclaimed_qubits(circuit, timestep)
    eligible_targets -= set(circuit.protected_qubits)
    eligible_targets.discard(signal_qubit)
    if not eligible_targets:
        raise ValueError(
            "no unprotected reclaimed qubit is eligible for payload injection"
        )

    target_qubit = min(eligible_targets)
    return circuit.insert_after(
        timestep,
        CircuitOperation("cnot", (signal_qubit, target_qubit)),
    )


__all__ = [
    "Circuit",
    "CircuitOperation",
    "identify_reclaimed_qubits",
    "inject_payload",
]
