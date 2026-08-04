#!/usr/bin/env python3
"""Compatibility facade for the legacy parameterized analysis module.

The canonical orchestration now lives in quantum_reuse.analysis.
This module is retained for backward compatibility with existing imports and
entry points while decomposition completes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analysis import (
    average_fifth_state,
    bob_probabilities,
    branch_trace_bob_result_probabilities,
    detector_acceptance_probability,
    detector_acceptance_probability_from_branch_trace,
    detector_acceptance_truth_table,
    detector_accepts,
    provisional_acceptance_probability,
    run_analysis,
    validate_quantum_computation,
)
from .circuits import apply_swap, ry, rz

__all__ = [
    "average_fifth_state",
    "bob_probabilities",
    "branch_trace_bob_result_probabilities",
    "detector_acceptance_probability",
    "detector_acceptance_probability_from_branch_trace",
    "detector_acceptance_truth_table",
    "detector_accepts",
    "provisional_acceptance_probability",
    "run_analysis",
    "validate_quantum_computation",
    "apply_swap",
    "ry",
    "rz",
    "qiskit_parameterized_skeleton",
    "qiskit_parameterized_circuit",
    "main",
]


def qiskit_parameterized_skeleton():
    """Return a Qiskit Parameter-based circuit when Qiskit is available."""
    try:
        from qiskit import QuantumCircuit  # type: ignore[import-not-found]
        from qiskit.circuit import Parameter  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Qiskit is not installed. Install qiskit locally to use this constructor."
        ) from exc

    theta = Parameter("theta")
    phi = Parameter("phi")
    eve_angle = Parameter("eve_angle")

    qc = QuantumCircuit(5, name="advanced_spy_parameterized")
    for target in (2, 3):
        qc.ry(theta, target)
        qc.rz(phi, target)

    # Keep this as a hook for experiments; exact branch behavior is evaluated
    # with the deterministic NumPy backend.
    qc.ry(eve_angle, 2)
    qc.swap(3, 4)
    qc.swap(2, 4)

    return qc, {"theta": theta, "phi": phi, "eve_angle": eve_angle}


def qiskit_parameterized_circuit():
    """Backward-compatible alias for qiskit_parameterized_skeleton()."""
    return qiskit_parameterized_skeleton()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("run_output"),
        help="Directory for CSV, JSON, Markdown, and graph outputs.",
    )
    args = parser.parse_args()
    summary = run_analysis(args.output)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
