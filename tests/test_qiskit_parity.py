"""Cross-backend parity tests: Qiskit Statevector vs NumPy reference model.

All tests require qiskit and are automatically skipped when it is not
installed.  To run them locally::

    pip install 'quantum-reuse-security[qiskit]'
    pytest tests/test_qiskit_parity.py -v
"""

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("qiskit", reason="qiskit not installed; skipping parity tests")

from quantum_reuse.analysis import average_fifth_state, run_analysis  # noqa: E402
from quantum_reuse.measurements import enumerate_eve_branches  # noqa: E402
from quantum_reuse.metrics import trace_distance  # noqa: E402
from quantum_reuse.qiskit_backend import (  # noqa: E402
    build_protocol_circuit,
    enumerate_eve_branches_qiskit,
    qiskit_available,
)

# Matches the NumPy model's own numerical-validation tolerance.
PARITY_TOLERANCE = 1e-10

_INPUTS = [(v, b, e) for v in (0, 1) for b in (0, 1) for e in (0, 1)]


# ---------------------------------------------------------------------------
# Smoke
# ---------------------------------------------------------------------------


def test_qiskit_available_returns_true() -> None:
    """qiskit_available() must be True if the import-skip passed."""
    assert qiskit_available()


def test_build_protocol_circuit_returns_five_qubit_circuit() -> None:
    from qiskit import QuantumCircuit

    for v in (0, 1):
        for b in (0, 1):
            for e in (0, 1):
                qc = build_protocol_circuit(v, b, e)
                assert isinstance(qc, QuantumCircuit)
                assert qc.num_qubits == 5


# ---------------------------------------------------------------------------
# Branch-level parity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value,basis,eve_basis", _INPUTS)
def test_branch_count_and_probabilities(value, basis, eve_basis) -> None:
    """Qiskit and NumPy yield the same number of branches and probabilities."""
    np_branches = enumerate_eve_branches(value, basis, eve_basis)
    qk_branches = enumerate_eve_branches_qiskit(value, basis, eve_basis)

    assert len(np_branches) == len(qk_branches)
    for nb, qb in zip(np_branches, qk_branches):
        assert abs(nb.branch_probability - qb.branch_probability) < PARITY_TOLERANCE


@pytest.mark.parametrize("value,basis,eve_basis", _INPUTS)
def test_fifth_rho_parity(value, basis, eve_basis) -> None:
    """Fifth-wire density matrices agree within PARITY_TOLERANCE."""
    np_branches = enumerate_eve_branches(value, basis, eve_basis)
    qk_branches = enumerate_eve_branches_qiskit(value, basis, eve_basis)

    for nb, qb in zip(np_branches, qk_branches):
        td = trace_distance(nb.fifth_rho, qb.fifth_rho)
        assert td < PARITY_TOLERANCE, (
            f"fifth_rho mismatch v={value} b={basis} e={eve_basis} "
            f"r_E={nb.eve_result}: trace_distance={td:.2e}"
        )


@pytest.mark.parametrize("value,basis,eve_basis", _INPUTS)
def test_victim_rho_parity(value, basis, eve_basis) -> None:
    """Victim-subsystem density matrices agree within PARITY_TOLERANCE."""
    np_branches = enumerate_eve_branches(value, basis, eve_basis)
    qk_branches = enumerate_eve_branches_qiskit(value, basis, eve_basis)

    for nb, qb in zip(np_branches, qk_branches):
        td = trace_distance(nb.victim_rho, qb.victim_rho)
        assert td < PARITY_TOLERANCE, (
            f"victim_rho mismatch v={value} b={basis} e={eve_basis} "
            f"r_E={nb.eve_result}: trace_distance={td:.2e}"
        )


@pytest.mark.parametrize("value,basis,eve_basis", _INPUTS)
def test_victim_fidelity_parity(value, basis, eve_basis) -> None:
    """Victim-subsystem fidelity values match between backends."""
    np_branches = enumerate_eve_branches(value, basis, eve_basis)
    qk_branches = enumerate_eve_branches_qiskit(value, basis, eve_basis)

    for nb, qb in zip(np_branches, qk_branches):
        assert abs(nb.victim_fidelity - qb.victim_fidelity) < PARITY_TOLERANCE


# ---------------------------------------------------------------------------
# Aggregate parity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("value,basis,eve_basis", _INPUTS)
def test_average_fifth_state_parity(value, basis, eve_basis) -> None:
    """Average fifth-wire state matches between backends."""
    np_avg = average_fifth_state(value, basis, eve_basis)
    qk_branches = enumerate_eve_branches_qiskit(value, basis, eve_basis)
    qk_avg = np.zeros((2, 2), dtype=complex)
    for b in qk_branches:
        qk_avg += b.branch_probability * b.fifth_rho

    td = trace_distance(np_avg, qk_avg)
    assert td < PARITY_TOLERANCE, (
        f"average_fifth_state mismatch v={value} b={basis} "
        f"e={eve_basis}: trace_distance={td:.2e}"
    )


def test_all_branch_probabilities_sum_to_one() -> None:
    """Qiskit branch probabilities sum to 1 for every input."""
    for v, b, e in _INPUTS:
        total = sum(
            br.branch_probability for br in enumerate_eve_branches_qiskit(v, b, e)
        )
        assert abs(total - 1.0) < PARITY_TOLERANCE


# ---------------------------------------------------------------------------
# End-to-end run_analysis CSV parity
# ---------------------------------------------------------------------------

_CSV_ARTIFACTS = [
    "branch_conditioned_results.csv",
    "averaged_fifth_wire_states.csv",
    "distinguishability_metrics.csv",
]


def test_run_analysis_csv_parity(tmp_path) -> None:
    """run_analysis(backend='qiskit') CSV outputs match run_analysis(backend='numpy').

    Verifies that the full analysis pipeline produces identical branch tables
    and summary metrics regardless of which simulation backend is selected.
    Numeric columns are compared with atol=1e-10; string columns must be equal.
    """
    np_dir = tmp_path / "numpy_out"
    qk_dir = tmp_path / "qiskit_out"
    import matplotlib

    matplotlib.use("Agg")
    run_analysis(np_dir, backend="numpy")
    run_analysis(qk_dir, backend="qiskit")

    for artifact in _CSV_ARTIFACTS:
        left = pd.read_csv(np_dir / artifact)
        right = pd.read_csv(qk_dir / artifact)

        assert list(left.columns) == list(right.columns), f"{artifact}: column mismatch"
        for col in left.columns:
            if pd.api.types.is_numeric_dtype(left[col]):
                assert np.allclose(
                    left[col].to_numpy(),
                    right[col].to_numpy(),
                    rtol=0.0,
                    atol=PARITY_TOLERANCE,
                    equal_nan=True,
                ), (
                    f"{artifact}:{col}: numpy vs qiskit numeric mismatch "
                    f"(max delta "
                    f"{float(np.abs(left[col].to_numpy() - right[col].to_numpy()).max()):.2e})"  # noqa: E501
                )
            else:
                assert (
                    left[col].astype(str).equals(right[col].astype(str))
                ), f"{artifact}:{col}: numpy vs qiskit text mismatch"
