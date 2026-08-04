import numpy as np

from quantum_reuse.parameterized_fifth_wire_analysis import (
    branch_trace_bob_result_probabilities,
    bob_probabilities,
    detector_acceptance_probability,
    detector_acceptance_probability_from_branch_trace,
    detector_acceptance_truth_table,
    detector_accepts,
)


def test_detector_accept_boolean_truth_table_matches_expression() -> None:
    rows = detector_acceptance_truth_table()
    assert len(rows) == 16
    for row in rows:
        v = row["v"]
        b = row["b"]
        c = row["c"]
        r_b = row["r_B"]
        expected = int((c != b) or (r_b == v))
        assert row["accept"] == expected
        assert int(detector_accepts(v, b, c, r_b)) == expected


def test_detector_acceptance_probability_uses_exact_boolean_event() -> None:
    for v in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                p0, p1 = bob_probabilities(v, b, c)
                expected = p0 * int((c != b) or (0 == v)) + p1 * int(
                    (c != b) or (1 == v)
                )
                actual = detector_acceptance_probability(v, b, c)
                assert np.isclose(actual, expected, atol=1e-12)


def test_detector_acceptance_is_unity_for_basis_mismatch() -> None:
    for v in (0, 1):
        for b in (0, 1):
            c = 1 - b
            assert np.isclose(detector_acceptance_probability(v, b, c), 1.0, atol=1e-12)


def test_branch_trace_bob_result_probabilities_are_normalized() -> None:
    for v in (0, 1):
        for b in (0, 1):
            for e in (0, 1):
                total_branch_weight = 0.0
                for r_e in (0, 1):
                    p_branch, p0, p1 = branch_trace_bob_result_probabilities(
                        v, b, e, r_e, b
                    )
                    total_branch_weight += p_branch
                    if p_branch > 0:
                        assert np.isclose(p0 + p1, 1.0, atol=1e-12)
                assert np.isclose(total_branch_weight, 1.0, atol=1e-12)


def test_detector_acceptance_formula_matches_branch_trace() -> None:
    for v in (0, 1):
        for b in (0, 1):
            for e in (0, 1):
                for c in (0, 1):
                    formula = detector_acceptance_probability(v, b, c)
                    trace = detector_acceptance_probability_from_branch_trace(
                        v, b, e, c
                    )
                    assert np.isclose(formula, trace, atol=1e-12)
