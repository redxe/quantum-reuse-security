"""Static consistency checks for the LaTeX research package.

This audit does not replace LaTeX's own reference and citation checks. It catches
common packaging mistakes before compilation: missing inputs, missing graphics,
duplicate labels, unresolved internal references, and stale filenames.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def collect(pattern: str, text: str) -> list[str]:
    return re.findall(pattern, text)


def audit(root: Path) -> tuple[str, bool]:
    tex_files = sorted(root.rglob("*.tex"))
    errors: list[str] = []
    warnings: list[str] = []
    labels: dict[str, Path] = {}
    references: list[tuple[str, Path]] = []

    for path in tex_files:
        text = path.read_text(encoding="utf-8")

        for label in collect(r"\\label\{([^}]+)\}", text):
            if label in labels:
                errors.append(f"Duplicate label {label}: {labels[label]} and {path}")
            labels[label] = path

        for command in ("ref", "eqref", "cref", "Cref", "pageref"):
            for group in collect(rf"\\{command}\{{([^}}]+)\}}", text):
                for ref in group.split(","):
                    references.append((ref.strip(), path))

        for target in collect(r"\\(?:input|include)\{([^}]+)\}", text):
            candidate = (path.parent / target)
            if candidate.suffix == "":
                candidate = candidate.with_suffix(".tex")
            if not candidate.exists():
                # Most project inputs are relative to ROOT, not the chapter file.
                candidate = root / target
                if candidate.suffix == "":
                    candidate = candidate.with_suffix(".tex")
            if not candidate.exists():
                errors.append(f"Missing TeX input {target} referenced by {path}")

        for target in collect(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", text):
            candidates = [root / target, root / "figures" / target]
            if not any(c.exists() for c in candidates):
                errors.append(f"Missing graphic {target} referenced by {path}")

        stale = {
            "src/analyze_quirk_exports.py": "src/build_case_study_ii.py",
            "Research Draft 0.5": "Research Draft 0.7",
            "Research Draft 0.6": "Research Draft 0.7",
            "grayscale reduced": "colored reduced",
        }
        for old, replacement in stale.items():
            if old in text:
                warnings.append(f"Stale text in {path}: {old!r}; expected {replacement!r}")

    for ref, path in references:
        if ref and ref not in labels:
            errors.append(f"Unresolved internal reference {ref} in {path}")

    report = [
        f"TeX files checked: {len(tex_files)}",
        f"Labels found: {len(labels)}",
        f"Internal references checked: {len(references)}",
        f"Errors: {len(errors)}",
        f"Warnings: {len(warnings)}",
    ]
    if errors:
        report.append("\nERRORS")
        report.extend(f"- {item}" for item in errors)
    if warnings:
        report.append("\nWARNINGS")
        report.extend(f"- {item}" for item in warnings)

    return "\n".join(report) + "\n", bool(errors)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="manuscript root to audit (default: the containing paper directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="report destination (default: <root>/data/manuscript_audit.txt)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output_path = args.output or root / "data" / "manuscript_audit.txt"
    output, has_errors = audit(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")
    print(output, end="")
    if has_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
