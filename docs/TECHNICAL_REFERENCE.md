# Technical Reference

## Scope

This document summarizes the executable technical core of this repository: deterministic branch-conditioned simulation, reduced-state extraction, fixed-input leakage characterization, and numerical validation.

## Canonical Entry Point

Run the analysis with:

```bash
python -m quantum_reuse analyze --output run_output
```

The command emits deterministic artifacts including branch-conditioned CSV outputs, distinguishability metrics, summary JSON, validation JSON, plots, and a markdown run report.

## Fixed-Input Theorem (Executable Form)

For fixed Alice value v, Alice basis b, and Eve basis e, define the averaged fifth-wire reduced state as rho_5^(v,b,e).

The implemented and tested result is:

- rho_5^(v,b,e) = |v><v| if e = b
- rho_5^(v,b,e) = I/2 if e != b

This is enforced by regression tests and can be summarized with:

```bash
python -m quantum_reuse fixed-input-summary
```

## Victim-Subsystem Invariance (Within Numeric Precision)

Per branch, the script computes victim fidelity and trace distance to the clean routed baseline. Current runs show invariance up to floating-point precision limits.

## Numerical Validation

Validation checks include:

- trace normalization
- Hermiticity
- positive semidefinite eigenvalue checks
- perturbation-bound estimates

Detailed implementation references:

- src/quantum_reuse/validation.py
- src/quantum_reuse/parameterized_fifth_wire_analysis.py

## Reproducibility Notes

- Backend is exact linear algebra via NumPy.
- Outputs are deterministic for a fixed environment.
- CI compares regenerated deterministic outputs against committed data baselines.
