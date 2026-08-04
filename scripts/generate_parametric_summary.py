"""Generate a deterministic JSON summary of the parametric victim-channel sweep.

Outputs docs/paper/v0.7.0/data/parametric_victim_summary.json.
All counts and extrema are derived from the same code paths used by
tests/test_parametric_victim.py so the manuscript can cite them directly.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

# Make sure the src layout is on the path when run from the repo root.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quantum_reuse.measurements import enumerate_eve_branches_parametric  # noqa: E402

# ---------------------------------------------------------------------------
# Grid (must match test_parametric_victim.py exactly)
# ---------------------------------------------------------------------------
_THETA_GRID = [0.0, np.pi / 4, np.pi / 3, np.pi / 2, 2 * np.pi / 3, np.pi]
_PHI_GRID = [0.0, np.pi / 4, np.pi / 2, np.pi, 3 * np.pi / 2]
FIDELITY_TOL = 1e-10
TRACE_DIST_TOL = 1e-10
RANDOM_N = 200
RANDOM_SEED = 42
QISKIT_SEED = 7
QISKIT_N = 8


def _sweep(thetas, phis, label: str):
    """Run the sweep and return aggregated stats."""
    param_settings = 0
    realized_branches = 0
    min_fidelity = math.inf
    max_trace_distance = 0.0

    for theta, phi in zip(thetas, phis):
        for eve_basis in (0, 1):
            branches = enumerate_eve_branches_parametric(theta, phi, eve_basis)
            param_settings += 1
            realized_branches += len(branches)
            for b in branches:
                if b.victim_fidelity < min_fidelity:
                    min_fidelity = b.victim_fidelity
                if b.victim_trace_distance > max_trace_distance:
                    max_trace_distance = b.victim_trace_distance

    print(
        f"  {label}: {param_settings} settings, "
        f"{realized_branches} branches, "
        f"min_fid={min_fidelity:.6e}, max_td={max_trace_distance:.6e}"
    )
    return param_settings, realized_branches, min_fidelity, max_trace_distance


def main() -> None:
    # ---- Grid sweep ----
    grid_thetas = [t for t in _THETA_GRID for _ in _PHI_GRID]
    grid_phis = [p for _ in _THETA_GRID for p in _PHI_GRID]
    (
        grid_param_settings,
        grid_realized_branches,
        grid_min_fidelity,
        grid_max_trace_distance,
    ) = _sweep(grid_thetas, grid_phis, "grid")

    # ---- Random sweep ----
    rng = np.random.default_rng(RANDOM_SEED)
    rand_thetas = rng.uniform(0, np.pi, RANDOM_N)
    rand_phis = rng.uniform(0, 2 * np.pi, RANDOM_N)
    (
        rand_param_settings,
        rand_realized_branches,
        rand_min_fidelity,
        rand_max_trace_distance,
    ) = _sweep(rand_thetas, rand_phis, "random")

    # ---- Qiskit parity scope ----
    qk_rng = np.random.default_rng(QISKIT_SEED)
    qk_thetas = qk_rng.uniform(0, np.pi, QISKIT_N)
    qk_phis = qk_rng.uniform(0, 2 * np.pi, QISKIT_N)
    qk_param_settings = QISKIT_N * 2  # 2 Eve bases each
    qk_realized_branches = QISKIT_N * 2 * 2  # 2 Eve bases × 2 branches each

    # ---- Combined ----
    total_param_settings = grid_param_settings + rand_param_settings
    total_realized_branches = grid_realized_branches + rand_realized_branches
    combined_min_fidelity = min(grid_min_fidelity, rand_min_fidelity)
    combined_max_trace_distance = max(grid_max_trace_distance, rand_max_trace_distance)

    summary = {
        "grid_theta_values": len(_THETA_GRID),
        "grid_phi_values": len(_PHI_GRID),
        "grid_eve_bases": 2,
        "grid_parameter_settings": grid_param_settings,
        "grid_realized_branches": grid_realized_branches,
        "grid_min_fidelity": grid_min_fidelity,
        "grid_max_trace_distance": grid_max_trace_distance,
        "random_n_states": RANDOM_N,
        "random_seed": RANDOM_SEED,
        "random_eve_bases": 2,
        "random_parameter_settings": rand_param_settings,
        "random_realized_branches": rand_realized_branches,
        "random_min_fidelity": rand_min_fidelity,
        "random_max_trace_distance": rand_max_trace_distance,
        "total_parameter_settings": total_param_settings,
        "total_realized_branches": total_realized_branches,
        "combined_min_fidelity": combined_min_fidelity,
        "combined_max_trace_distance": combined_max_trace_distance,
        "fidelity_threshold": FIDELITY_TOL,
        "trace_distance_threshold": TRACE_DIST_TOL,
        "qiskit_n_states": QISKIT_N,
        "qiskit_seed": QISKIT_SEED,
        "qiskit_parameter_settings_checked": qk_param_settings,
        "qiskit_realized_branches_checked": qk_realized_branches,
    }

    out_path = (
        Path(__file__).parent.parent
        / "docs"
        / "paper"
        / "v0.7.0"
        / "data"
        / "parametric_victim_summary.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
        f.write("\n")

    print(f"\nWrote {out_path}")
    print(f"  total_parameter_settings = {total_param_settings}")
    print(f"  total_realized_branches  = {total_realized_branches}")
    print(f"  combined_min_fidelity    = {combined_min_fidelity:.6e}")
    print(f"  combined_max_trace_dist  = {combined_max_trace_distance:.6e}")
    print(f"  qiskit_param_settings    = {qk_param_settings}")


if __name__ == "__main__":
    main()
