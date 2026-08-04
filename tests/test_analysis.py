import numpy as np

from quantum_reuse.analysis import fixed_input_summary
from quantum_reuse.measurements import enumerate_eve_branches
from quantum_reuse.metrics import trace_distance
from quantum_reuse.parameterized_fifth_wire_analysis import (
    apply_swap,
    average_fifth_state,
)


def test_branch_probabilities_sum_to_one() -> None:
    for v in (0, 1):
        for b in (0, 1):
            for e in (0, 1):
                branches = enumerate_eve_branches(v, b, e)
                total = sum(branch.branch_probability for branch in branches)
                assert abs(total - 1.0) < 1e-12


def test_swap_network_permutation_q2_q3_q4() -> None:
    # Local 3-qubit labels represent (q2, q3, q4).
    # Network: SWAP(q3,q4) then SWAP(q2,q4) => (a,b,c) -> (b,c,a).
    n = 3
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                index = (a << 2) | (b << 1) | c
                state = np.zeros(2**n, dtype=complex)
                state[index] = 1.0

                routed = apply_swap(state, 1, 2, n)
                routed = apply_swap(routed, 0, 2, n)

                target_index = (b << 2) | (c << 1) | a
                target = np.zeros(2**n, dtype=complex)
                target[target_index] = 1.0
                assert np.allclose(routed, target, atol=1e-12)


def test_routing_places_eve_result_on_retained_wire() -> None:
    ket0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    ket1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    for v in (0, 1):
        for b in (0, 1):
            for e in (0, 1):
                for branch in enumerate_eve_branches(v, b, e):
                    target = ket1 if branch.eve_result == 1 else ket0
                    assert trace_distance(branch.fifth_rho, target) < 1e-12


def test_fifth_wire_matching_basis_reveals_value() -> None:
    ket0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    ket1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    for v in (0, 1):
        for b in (0, 1):
            rho = average_fifth_state(v, b, b)
            target = ket1 if v == 1 else ket0
            assert trace_distance(rho, target) < 1e-12


def test_fifth_wire_mismatched_basis_is_maximally_mixed() -> None:
    mm = 0.5 * np.eye(2, dtype=complex)
    for v in (0, 1):
        for b in (0, 1):
            rho = average_fifth_state(v, b, 1 - b)
            assert trace_distance(rho, mm) < 1e-12


def test_victim_subsystem_is_preserved() -> None:
    for v in (0, 1):
        for b in (0, 1):
            for e in (0, 1):
                for branch in enumerate_eve_branches(v, b, e):
                    assert branch.victim_fidelity > 1 - 1e-12
                    assert branch.victim_trace_distance < 1e-12


def test_fixed_input_summary_theorem_errors_are_small() -> None:
    summary = fixed_input_summary()
    assert summary["max_matching_trace_distance_error"] < 1e-12
    assert summary["max_mismatch_trace_distance_error"] < 1e-12
