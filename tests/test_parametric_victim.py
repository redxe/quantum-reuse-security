"""Issue #7: victim-channel preservation beyond the four BB84 inputs.

Establishes that the victim subsystem's read privilege (Bob's observable) is
preserved for arbitrary (theta, phi) signal-wire preparations, not only the
four fixed BB84 states.  This tests the open claim stated in
docs/THREAT_MODEL.md Section 7.

Cross-backend Qiskit parity tests are skipped automatically when qiskit is
not installed.
"""

from __future__ import annotations

import numpy as np
import pytest

from quantum_reuse.measurements import enumerate_eve_branches_parametric
from quantum_reuse.state_preparation import bb84_angles

FIDELITY_TOL = 1e-10
TRACE_DIST_TOL = 1e-10

# Grid of angles that spans non-BB84 points as well as the BB84 poles.
_THETA_GRID = [0.0, np.pi / 4, np.pi / 3, np.pi / 2, 2 * np.pi / 3, np.pi]
_PHI_GRID = [0.0, np.pi / 4, np.pi / 2, np.pi, 3 * np.pi / 2]

# ---------------------------------------------------------------------------
# Grid tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("eve_basis", [0, 1])
@pytest.mark.parametrize("phi", _PHI_GRID)
@pytest.mark.parametrize("theta", _THETA_GRID)
def test_victim_preservation_grid(theta, phi, eve_basis) -> None:
    """Victim fidelity >= 1 - 1e-10 for every grid (theta, phi) and eve_basis."""
    branches = enumerate_eve_branches_parametric(theta, phi, eve_basis)
    assert len(branches) >= 1, "At least one branch must exist"
    for b in branches:
        assert b.victim_fidelity > 1 - FIDELITY_TOL, (
            f"theta={theta:.4f} phi={phi:.4f} e={eve_basis} "
            f"r_E={b.eve_result}: fidelity={b.victim_fidelity:.8f}"
        )
        assert b.victim_trace_distance < TRACE_DIST_TOL, (
            f"theta={theta:.4f} phi={phi:.4f} e={eve_basis} "
            f"r_E={b.eve_result}: trace_distance={b.victim_trace_distance:.2e}"
        )


# ---------------------------------------------------------------------------
# Random continuous sweep
# ---------------------------------------------------------------------------


def test_victim_preservation_random_sweep() -> None:
    """Victim preservation holds for N=200 deterministically sampled inputs."""
    rng = np.random.default_rng(42)
    N = 200
    thetas = rng.uniform(0, np.pi, N)
    phis = rng.uniform(0, 2 * np.pi, N)

    failures: list[str] = []
    for i, (theta, phi) in enumerate(zip(thetas, phis)):
        for eve_basis in (0, 1):
            for b in enumerate_eve_branches_parametric(theta, phi, eve_basis):
                if b.victim_fidelity <= 1 - FIDELITY_TOL:
                    failures.append(
                        f"[{i}] theta={theta:.5f} phi={phi:.5f} "
                        f"e={eve_basis} r_E={b.eve_result} "
                        f"fidelity={b.victim_fidelity:.10f}"
                    )
                if b.victim_trace_distance >= TRACE_DIST_TOL:
                    failures.append(
                        f"[{i}] theta={theta:.5f} phi={phi:.5f} "
                        f"e={eve_basis} r_E={b.eve_result} "
                        f"trace_distance={b.victim_trace_distance:.2e}"
                    )

    assert not failures, f"{len(failures)} failures (showing first 5):\n" + "\n".join(
        failures[:5]
    )


# ---------------------------------------------------------------------------
# Consistency: parametric at BB84 angles reproduces fixed-model victim state
# ---------------------------------------------------------------------------


def test_parametric_at_bb84_matches_fixed() -> None:
    """At BB84 angles, parametric model's q2 reduced state matches fixed model."""
    from quantum_reuse.measurements import enumerate_eve_branches
    from quantum_reuse.metrics import trace_distance

    for value in (0, 1):
        for basis in (0, 1):
            theta, phi = bb84_angles(value, basis)
            for eve_basis in (0, 1):
                fixed = enumerate_eve_branches(value, basis, eve_basis)
                parametric = enumerate_eve_branches_parametric(theta, phi, eve_basis)
                assert len(fixed) == len(
                    parametric
                ), f"v={value} b={basis} e={eve_basis}: branch count mismatch"
                for fb, pb in zip(fixed, parametric):
                    assert (
                        abs(fb.branch_probability - pb.branch_probability)
                        < TRACE_DIST_TOL
                    )
                    # Compare q2 (encoded state qubit) from the victim subsystem.
                    # victim_rho is 16x16 (q0..q3). Trace out q0, q1, q3 to get
                    # the 2x2 reduced state of q2, which carries the encoded signal.
                    fixed_q2 = _reduce_to_q2(fb.victim_rho)
                    param_q2 = _reduce_to_q2(pb.victim_rho)
                    td = trace_distance(fixed_q2, param_q2)
                    assert td < TRACE_DIST_TOL, (
                        f"v={value} b={basis} e={eve_basis} "
                        f"r_E={fb.eve_result}: q2 trace_distance={td:.2e}"
                    )


def _reduce_to_q2(victim_rho: np.ndarray) -> np.ndarray:
    """Return the 2x2 reduced state of q2 from the 4-qubit victim density matrix.

    Traces out q0, q1, q3 (big-endian ordering: q0=MSB, q3=LSB).
    """
    r = victim_rho.reshape(2, 2, 2, 2, 2, 2, 2, 2)
    # r[a,b,i,c, a,b,j,c] -> rho_q2[i,j]
    # a=q0, b=q1, i=q2_bra, c=q3, j=q2_ket (a,b,c contracted; i,j free)
    return np.einsum("abicabjc->ij", r)


# ---------------------------------------------------------------------------
# Qiskit parity for parametric inputs
# ---------------------------------------------------------------------------


def test_qiskit_parametric_parity() -> None:
    """Qiskit Statevector backend agrees with NumPy for parametric inputs."""
    pytest.importorskip("qiskit", reason="qiskit not installed")
    from quantum_reuse.metrics import trace_distance
    from quantum_reuse.qiskit_backend import enumerate_eve_branches_qiskit_parametric

    rng = np.random.default_rng(7)
    sample_thetas = rng.uniform(0, np.pi, 8)
    sample_phis = rng.uniform(0, 2 * np.pi, 8)

    for theta, phi in zip(sample_thetas, sample_phis):
        for eve_basis in (0, 1):
            np_branches = enumerate_eve_branches_parametric(theta, phi, eve_basis)
            qk_branches = enumerate_eve_branches_qiskit_parametric(
                theta, phi, eve_basis
            )
            assert len(np_branches) == len(qk_branches)
            for nb, qb in zip(np_branches, qk_branches):
                assert abs(nb.branch_probability - qb.branch_probability) < FIDELITY_TOL
                td = trace_distance(nb.victim_rho, qb.victim_rho)
                assert td < FIDELITY_TOL, (
                    f"theta={theta:.4f} phi={phi:.4f} e={eve_basis} "
                    f"r_E={nb.eve_result}: victim_rho td={td:.2e}"
                )
