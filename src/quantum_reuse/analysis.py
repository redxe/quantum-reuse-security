"""Top-level experiments and reproducibility helpers."""

from pathlib import Path

import numpy as np

from .parameterized_fifth_wire_analysis import run_analysis as _run_analysis
from .metrics import average_fifth_state, trace_distance


def fixed_input_summary() -> dict:
    """Return theorem-level fixed-input summary for the fifth-wire state."""
    max_matching_error = 0.0
    max_mismatch_error = 0.0

    ket0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    ket1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    maximally_mixed = 0.5 * np.eye(2, dtype=complex)

    for v in (0, 1):
        for b in (0, 1):
            for e in (0, 1):
                rho = average_fifth_state(v, b, e)
                if e == b:
                    target = ket1 if v == 1 else ket0
                    max_matching_error = max(max_matching_error, trace_distance(rho, target))
                else:
                    max_mismatch_error = max(max_mismatch_error, trace_distance(rho, maximally_mixed))

    return {
        "rho5_theorem": "rho_5^(v,b,e) = |v><v| if e=b, else I/2",
        "max_matching_trace_distance_error": float(max_matching_error),
        "max_mismatch_trace_distance_error": float(max_mismatch_error),
    }


def run_analysis(output_dir: Path) -> dict:
    """Run the deterministic branch-conditioned analysis."""
    return _run_analysis(output_dir)
