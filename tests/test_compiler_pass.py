"""Issue #14: prototype malicious qubit-reuse compiler transformation.

Tests that:
  1. CNOT(q_signal → q_ancilla) does not disturb Bob's (victim) reduced state
     for all four BB84 inputs.
  2. The injected ancilla carries perfect value information (TD = 1) when
     Alice uses the Z basis, and no information (TD = 0) when Alice uses the
     X basis — matching the no-cloning structure.
  3. Victim preservation holds for a parametric sweep of arbitrary pure-state
     inputs (connecting to the Issue #7 result).
  4. The honest circuit always leaves the ancilla in |0><0|.
  5. Privilege conversion label is correct.
"""

from __future__ import annotations

import numpy as np
import pytest

from quantum_reuse.compiler_pass import analyze_injection, analyze_injection_parametric

_TOL = 1e-10

# All four BB84 (value, basis) combinations
_BB84 = [(v, b) for v in (0, 1) for b in (0, 1)]

# ── BB84 fixed-input tests ──────────────────────────────────────────────────


@pytest.mark.parametrize("value,basis", _BB84)
def test_victim_preserved_uses_trace_distance(value, basis) -> None:
    """victim_preserved must be based on direct state TD, not fidelity difference."""
    result = analyze_injection(value, basis)
    assert result.victim_trace_distance < _TOL, (
        f"v={value} b={basis}: victim TD honest-vs-injected = "
        f"{result.victim_trace_distance:.2e}"
    )
    assert result.victim_preserved


@pytest.mark.parametrize("value,basis", _BB84)
def test_victim_preserved_after_injection(value, basis) -> None:
    """CNOT(q2\u2192q4) must not disturb Bob's signal qubit (q3) for any BB84 input."""
    result = analyze_injection(value, basis)
    assert result.victim_preserved, (
        f"v={value} b={basis}: victim fidelity "
        f"honest={result.victim_fidelity_honest:.10f} "
        f"injected={result.victim_fidelity_injected:.10f}"
    )
    assert result.victim_fidelity_injected > 1 - _TOL, (
        f"v={value} b={basis}: victim fidelity after injection = "
        f"{result.victim_fidelity_injected:.10f}"
    )


@pytest.mark.parametrize("value,basis", _BB84)
def test_honest_ancilla_is_zero(value, basis) -> None:
    """Honest circuit: ancilla q4 must equal |0><0| (never touched)."""
    result = analyze_injection(value, basis)
    zero_rho = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    from quantum_reuse.metrics import trace_distance as _td

    td = _td(result.ancilla_rho_honest, zero_rho)
    assert td < _TOL, (
        f"v={value} b={basis}: honest ancilla deviates from " f"|0><0| by td={td:.2e}"
    )


def test_z_basis_attacker_advantage_perfect() -> None:
    """Z-basis: ancilla states for v=0 vs v=1 are perfectly distinguishable."""
    result_0 = analyze_injection(0, basis=0)
    result_1 = analyze_injection(1, basis=0)
    # Both should report TD = 1 (they compute the same cross-value comparison)
    assert (
        abs(result_0.attacker_trace_distance - 1.0) < _TOL
    ), f"Z-basis attacker TD = {result_0.attacker_trace_distance:.6f}, expected 1"
    assert abs(result_1.attacker_trace_distance - 1.0) < _TOL


def test_x_basis_attacker_advantage_zero() -> None:
    """X-basis injection: ancilla is maximally mixed; attacker gains no value info."""
    result_0 = analyze_injection(0, basis=1)
    result_1 = analyze_injection(1, basis=1)
    assert (
        result_0.attacker_trace_distance < _TOL
    ), f"X-basis attacker TD = {result_0.attacker_trace_distance:.2e}, expected ~0"
    assert result_1.attacker_trace_distance < _TOL


def test_z_basis_ancilla_carries_signal() -> None:
    """Z-basis: injected ancilla state is |v><v|, confirming value retention."""
    from quantum_reuse.metrics import trace_distance

    for value in (0, 1):
        result = analyze_injection(value, basis=0)
        expected = np.zeros((2, 2), dtype=complex)
        expected[value, value] = 1.0
        td = trace_distance(result.ancilla_rho_injected, expected)
        assert (
            td < _TOL
        ), f"v={value} b=0: ancilla TD from |{value}><{value}| = {td:.2e}"


def test_x_basis_ancilla_is_maximally_mixed() -> None:
    """X-basis: injected ancilla is I/2 (entangled with signal; no classical copy)."""
    from quantum_reuse.metrics import trace_distance

    half_id = np.eye(2, dtype=complex) / 2
    for value in (0, 1):
        result = analyze_injection(value, basis=1)
        td = trace_distance(result.ancilla_rho_injected, half_id)
        assert td < _TOL, f"v={value} b=1: ancilla TD from I/2 = {td:.2e}"


def test_privilege_label_z_basis() -> None:
    """Z-basis: label must say retain(v) and note export is not modeled."""
    result = analyze_injection(0, basis=0)
    assert "retain(v)" in result.privilege_converted
    assert "export not modeled" in result.privilege_converted


def test_privilege_label_x_basis() -> None:
    """X-basis: label must say 'use only; no retain(v)'."""
    result = analyze_injection(0, basis=1)
    assert "use only" in result.privilege_converted
    assert "no retain(v)" in result.privilege_converted


# ── Parametric sweep ────────────────────────────────────────────────────────

_THETA_GRID = [0.0, np.pi / 4, np.pi / 3, np.pi / 2, 2 * np.pi / 3, np.pi]
_PHI_GRID = [0.0, np.pi / 4, np.pi / 2, np.pi, 3 * np.pi / 2]


@pytest.mark.parametrize("phi", _PHI_GRID)
@pytest.mark.parametrize("theta", _THETA_GRID)
def test_parametric_victim_preserved_after_injection(theta, phi) -> None:
    """CNOT(q2→q4) does not disturb Bob's qubit for arbitrary pure-state inputs."""
    victim_preserved, fidelity, _ = analyze_injection_parametric(theta, phi)
    assert (
        victim_preserved
    ), f"theta={theta:.4f} phi={phi:.4f}: victim fidelity={fidelity:.10f}"
    assert fidelity > 1 - _TOL


@pytest.mark.parametrize("phi", _PHI_GRID)
@pytest.mark.parametrize("theta", _THETA_GRID)
def test_parametric_ancilla_deviates_from_zero(theta, phi) -> None:
    """For non-|0> inputs, the injected ancilla must deviate from |0><0|."""
    # At theta=0 the signal IS |0>, so CNOT has no effect — ancilla stays |0>.
    # For all other theta, the signal has a |1> component and the ancilla changes.
    _, _, att_td = analyze_injection_parametric(theta, phi)
    if abs(theta) < 1e-12:
        # Signal is |0>; CNOT has no effect; ancilla remains |0><0|
        assert att_td < _TOL, f"theta~0: expected att_td~0, got {att_td:.2e}"
    elif abs(theta - np.pi) < 1e-12:
        # Signal is |1>; CNOT flips ancilla to |1>; TD from |0><0| = 1
        assert att_td > 1 - _TOL, f"theta~pi: expected att_td~1, got {att_td:.2e}"
    else:
        # General case: ancilla is entangled; TD from |0><0| is in (0, 1)
        assert att_td > _TOL, (
            f"theta={theta:.4f} phi={phi:.4f}: ancilla unexpectedly unchanged "
            f"(att_td={att_td:.2e})"
        )


def test_parametric_random_sweep_victim_preserved() -> None:
    """Victim preservation holds for 200 pseudorandom inputs (seed 42)."""
    rng = np.random.default_rng(42)
    N = 200
    thetas = rng.uniform(0, np.pi, N)
    phis = rng.uniform(0, 2 * np.pi, N)

    failures: list[str] = []
    for i, (theta, phi) in enumerate(zip(thetas, phis)):
        preserved, fid, _ = analyze_injection_parametric(theta, phi)
        if not preserved or fid <= 1 - _TOL:
            failures.append(f"[{i}] theta={theta:.5f} phi={phi:.5f} fid={fid:.10f}")

    assert not failures, f"{len(failures)} victim-preservation failures:\n" + "\n".join(
        failures[:5]
    )
