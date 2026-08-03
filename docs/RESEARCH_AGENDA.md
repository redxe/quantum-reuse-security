# Research Agenda

## Current Position

The project has completed the fixed-input, branch-conditioned Stage 1 baseline and now needs engineering rigor plus targeted detector reconstruction.

## Completed Work (Stage 1)

- Semantic wire mapping in the corrected circuit model.
- Deterministic branch enumeration over $(v,b,e,r_E)$.
- Fixed-input theorem result for fifth-wire leakage:
  - $\rho_5^{(v,b,e)} = |v\rangle\langle v|$ when $e=b$.
  - $\rho_5^{(v,b,e)} = I/2$ when $e\neq b$.
- Victim-subsystem preservation checks per branch.
- Numerical validation report generation.

## Immediate Next Work

### A. Exact Detector Reconstruction (Highest Scientific Priority)

1. Reconstruct all classical output bits from the original educational example.
2. Identify the exact bit/comparison representing detection.
3. Express it as a Boolean function.
4. Compare baseline/intercept-resend/advanced acceptance under that exact detector.
5. Report acceptance and full victim-state fidelity together.

### B. Stage 2 Information Metrics

- Compute expanded information metrics from deterministic branch states.
- Keep fifth-wire theorem as a hard regression guard.

### C. Stage 3 Prototype and Stage 4 Hardware

- Build controlled malicious-compiler insertion prototype.
- Validate attack/defense behavior under noise and hardware constraints.

## Engineering Requirements For Reproducibility

- Keep deterministic CLI contract stable:
  - `python -m quantum_reuse analyze --output <dir>`
- Preserve regression tests for theorem and victim invariance.
- Keep CI output comparison against committed baselines.
