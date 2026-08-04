"""Command-line entry points for the quantum_reuse package."""

import argparse
import json
from pathlib import Path

from .analysis import fixed_input_summary, run_analysis


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quantum_reuse")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser(
        "analyze",
        help="Run deterministic branch-conditioned analysis and emit outputs.",
    )
    analyze.add_argument(
        "--output",
        type=Path,
        default=Path("run_output"),
        help="Output directory for CSV, JSON, Markdown, and PNG artifacts.",
    )
    analyze.add_argument(
        "--backend",
        choices=["numpy", "qiskit"],
        default="numpy",
        help=(
            "Simulation backend: 'numpy' (default, exact NumPy linear algebra) "
            "or 'qiskit' (Qiskit Statevector; requires the qiskit extra)."
        ),
    )

    subparsers.add_parser(
        "fixed-input-summary",
        help="Print theorem-level fixed-input leakage summary.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        summary = run_analysis(args.output, backend=args.backend)
        print(json.dumps(summary, indent=2))
        return

    if args.command == "fixed-input-summary":
        print(json.dumps(fixed_input_summary(), indent=2))
        return

    parser.error("Unknown command")
