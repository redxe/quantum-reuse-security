import numpy as np

from quantum_reuse.analysis import fixed_input_summary
from quantum_reuse.measurements import enumerate_eve_branches
from quantum_reuse.metrics import average_fifth_state, trace_distance


def test_branch_probabilities_sum_to_one() -> None:
    for v in (0, 1):
        for b in (0, 1):
            for e in (0, 1):
                branches = enumerate_eve_branches(v, b, e)
                total = sum(branch.branch_probability for branch in branches)
                assert abs(total - 1.0) < 1e-12


def test_swap_semantic_mapping() -> None:
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
