"""Example: run full deterministic branch-conditioned analysis."""

from pathlib import Path

from quantum_reuse.analysis import run_analysis

if __name__ == "__main__":
    summary = run_analysis(Path("run_output"))
    print("Analysis complete.")
    print(f"Computation valid: {summary['numerical_validation']['all_valid']}")
