import hashlib
import json

from quantum_reuse.analysis import run_analysis as run_analysis_new
from quantum_reuse.parameterized_fifth_wire_analysis import (
    run_analysis as run_analysis_old,
)


def _file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_analysis_entrypoints_are_compatible(tmp_path) -> None:
    new_output = tmp_path / "new"
    old_output = tmp_path / "old"

    new_summary = run_analysis_new(new_output)
    old_summary = run_analysis_old(old_output)

    assert new_summary == old_summary

    generated_files = [
        "branch_conditioned_results.csv",
        "averaged_fifth_wire_states.csv",
        "distinguishability_metrics.csv",
        "detector_acceptance_truth_table.csv",
        "detector_acceptance_consistency.csv",
        "information_summary.json",
        "numerical_validation.json",
        "run_summary.json",
        "run_report.md",
        "fifth_wire_bloch_z.png",
        "trace_distance_summary.png",
    ]

    for name in generated_files:
        new_file = new_output / name
        old_file = old_output / name
        assert new_file.exists()
        assert old_file.exists()
        assert _file_digest(new_file) == _file_digest(old_file)

    # Keep a direct semantic check for JSON payload stability across entrypoints.
    assert json.loads(
        (new_output / "run_summary.json").read_text(encoding="utf-8")
    ) == json.loads((old_output / "run_summary.json").read_text(encoding="utf-8"))
