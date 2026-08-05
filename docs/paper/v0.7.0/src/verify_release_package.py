"""Validate the manuscript release inventory and generated source records."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path, PurePosixPath


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
BOOKKEEPING_ENTRIES = frozenset({"MANIFEST.txt", "SHA256SUMS.txt"})
REQUIRED_SOURCE_ENTRIES = frozenset(
    {
        "README.md",
        "main.tex",
        "main.bbl",
        "preamble.tex",
        "references.bib",
        "src/audit_manuscript.py",
        "src/build_case_study_ii.py",
        "src/simulate_case_studies.py",
        "src/verify_release_package.py",
    }
)
GENERATED_RECORDS = (
    "data/bb84_case_study_results.csv",
    "data/hidden_correlation_curve.csv",
    "data/teleport_cleanup_results.csv",
    "data/case_study_ii_circuit_columns.json",
    "data/case_study_ii_exact_metrics.csv",
    "data/case_study_ii_output_amplitudes.json",
    "figures/case_study_ii_branch_amplitudes.tex",
    "figures/case_study_ii_circuits.tex",
    "figures/case_study_ii_density_matrices.tex",
    "figures/case_study_ii_probability_densities.tex",
)
NUMERIC_ABS_TOLERANCE = 1e-12


def is_safe_relative_path(entry: str) -> bool:
    path = PurePosixPath(entry)
    return bool(entry) and "\\" not in entry and not path.is_absolute() and ".." not in path.parts


def read_manifest(root: Path) -> tuple[list[str], list[str]]:
    entries: list[str] = []
    errors: list[str] = []
    seen: set[str] = set()

    for raw_entry in (root / "MANIFEST.txt").read_text(encoding="utf-8").splitlines():
        entry = raw_entry.strip()
        if not entry:
            continue
        if not is_safe_relative_path(entry):
            errors.append(f"unsafe manifest path: {entry!r}")
            continue
        if entry in seen:
            errors.append(f"duplicate manifest entry: {entry}")
            continue
        seen.add(entry)
        entries.append(entry)

    return entries, errors


def check_manifest(root: Path) -> list[str]:
    entries, errors = read_manifest(root)
    entry_set = set(entries)
    missing_required = sorted(REQUIRED_SOURCE_ENTRIES - entry_set)
    forbidden_bookkeeping = sorted(entry_set & BOOKKEEPING_ENTRIES)

    for entry in missing_required:
        errors.append(f"required source entry missing from manifest: {entry}")
    for entry in forbidden_bookkeeping:
        errors.append(f"bookkeeping entry must remain outside the release inventory: {entry}")

    root_resolved = root.resolve()
    for entry in entries:
        candidate = (root / entry).resolve()
        if root_resolved not in candidate.parents and candidate != root_resolved:
            errors.append(f"manifest path escapes manuscript root: {entry}")
        elif not candidate.is_file():
            errors.append(f"manifest entry is missing after generation: {entry}")

    return errors


def canonical_text_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def numbers_match(expected: float, actual: float) -> bool:
    if math.isnan(expected) or math.isnan(actual):
        return math.isnan(expected) and math.isnan(actual)
    return math.isclose(expected, actual, rel_tol=0.0, abs_tol=NUMERIC_ABS_TOLERANCE)


def csv_values_match(expected: str, actual: str) -> bool:
    try:
        return numbers_match(float(expected), float(actual))
    except ValueError:
        return expected == actual


def csv_records_match(source: Path, generated: Path) -> bool:
    with source.open(encoding="utf-8", newline="") as source_file:
        expected_rows = list(csv.reader(source_file))
    with generated.open(encoding="utf-8", newline="") as generated_file:
        actual_rows = list(csv.reader(generated_file))

    if len(expected_rows) != len(actual_rows):
        return False
    return all(
        len(expected_row) == len(actual_row)
        and all(
            csv_values_match(expected_value, actual_value)
            for expected_value, actual_value in zip(expected_row, actual_row)
        )
        for expected_row, actual_row in zip(expected_rows, actual_rows)
    )


def json_values_match(expected: object, actual: object) -> bool:
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return numbers_match(float(expected), float(actual))
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(
            json_values_match(expected_item, actual_item)
            for expected_item, actual_item in zip(expected, actual)
        )
    if isinstance(expected, dict) and isinstance(actual, dict):
        return expected.keys() == actual.keys() and all(
            json_values_match(expected[key], actual[key]) for key in expected
        )
    return expected == actual


def generated_records_match(source: Path, generated: Path) -> bool:
    if source.suffix == ".csv":
        return csv_records_match(source, generated)
    if source.suffix == ".json":
        return json_values_match(
            json.loads(source.read_text(encoding="utf-8")),
            json.loads(generated.read_text(encoding="utf-8")),
        )
    return canonical_text_bytes(source) == canonical_text_bytes(generated)


def check_generated_records(source_root: Path, generated_root: Path) -> list[str]:
    errors: list[str] = []
    for entry in GENERATED_RECORDS:
        source = source_root / entry
        generated = generated_root / entry
        if not source.is_file():
            errors.append(f"committed generated record is missing: {entry}")
        elif not generated.is_file():
            errors.append(f"generated record is missing: {entry}")
        elif not generated_records_match(source, generated):
            errors.append(f"generated record drift: {entry}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="release package root")
    parser.add_argument(
        "--check-generated",
        action="store_true",
        help="compare generated records in --root against --source-root",
    )
    parser.add_argument(
        "--records-only",
        action="store_true",
        help="skip the full manifest check and validate generated records only",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        help="committed manuscript root used with --check-generated",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    errors = [] if args.records_only else check_manifest(root)

    if args.check_generated:
        if args.source_root is None:
            raise SystemExit("--source-root is required with --check-generated")
        errors.extend(check_generated_records(args.source_root.resolve(), root))

    if errors:
        print("Release package verification failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("Release package verification passed.")


if __name__ == "__main__":
    main()