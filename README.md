# Known-State Qubits as Both Resource and Risk

Deterministic branch-conditioned analysis for quantum qubit reuse security.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/redxe/quantum-reuse-security/actions/workflows/ci.yml/badge.svg)](https://github.com/redxe/quantum-reuse-security/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/redxe/quantum-reuse-security?sort=semver)](https://github.com/redxe/quantum-reuse-security/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

This repository focuses on reproducible software evidence for a source-access threat model in quantum circuits.

What is currently implemented and validated:

- Exact branch-conditioned analysis with a NumPy reference backend.
- Fixed-input fifth-wire theorem tested in code:
  - $\rho_5^{(v,b,e)} = |v\rangle\langle v|$ when $e=b$.
  - $\rho_5^{(v,b,e)} = I/2$ when $e\neq b$.
- Victim-subsystem preservation in the reconstructed branch model within floating-point precision.
- Numerical validation checks on every computed density matrix.

## Repository Structure

```text
.
├── .github/ISSUE_TEMPLATE/
│   ├── detector-register-reconstruction.md
│   ├── monolith-decomposition.md
│   └── qiskit-parity.md
├── .github/workflows/ci.yml
├── CITATION.cff
├── CHANGELOG.md
├── LICENSE
├── README.md
├── pyproject.toml
├── requirements.txt
├── setup.py
├── data/
│   ├── averaged_fifth_wire_states.csv
│   ├── branch_conditioned_results.csv
│   ├── corrected_quirk_circuits.json
│   └── distinguishability_metrics.csv
├── docs/
│   ├── INTERVIEW_GUIDE.md
│   ├── PAPER.md
│   ├── RESEARCH_AGENDA.md
│   ├── RELEASE_NOTES_v0.6.0.md
│   ├── TECHNICAL_REFERENCE.md
│   ├── THREAT_MODEL.md
│   └── VALIDATION_FRAMEWORK.md
├── examples/
│   ├── coherent_teleportation.py
│   ├── information_leakage.py
│   └── spy_detector_analysis.py
├── src/quantum_reuse/
│   ├── __init__.py
│   ├── __main__.py
│   ├── analysis.py
│   ├── circuits.py
│   ├── cli.py
│   ├── measurements.py
│   ├── metrics.py
│   ├── parameterized_fifth_wire_analysis.py
│   ├── state_preparation.py
│   └── validation.py
└── tests/
    ├── test_analysis.py
    ├── test_circuits.py
    └── test_validation.py
```

## Quickstart

### Install

```bash
git clone https://github.com/redxe/quantum-reuse-security.git
cd quantum-reuse-security
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

### Run Deterministic Analysis

```bash
python -m quantum_reuse analyze --output run_output
```

### Print Fixed-Input Theorem Summary

```bash
python -m quantum_reuse fixed-input-summary
```

### Run Tests

```bash
pytest -q
```

## Reproducibility Outputs

`python -m quantum_reuse analyze --output run_output` generates:

- `run_output/branch_conditioned_results.csv`
- `run_output/averaged_fifth_wire_states.csv`
- `run_output/distinguishability_metrics.csv`
- `run_output/information_summary.json`
- `run_output/numerical_validation.json`
- `run_output/run_summary.json`
- `run_output/run_report.md`
- `run_output/fifth_wire_bloch_z.png`
- `run_output/trace_distance_summary.png`

CI reruns the analysis and checks regenerated deterministic CSV artifacts against committed baselines in `data/`.

## Current Scientific Status

### Implementation Note: Coherent Cleanup vs Reference Transfer

Two three-qubit helpers are kept intentionally:

- `coherent_teleportation_cleanup_quirk(...)`: exact reconstructed Quirk-sequence
  coherent cleanup implementation.
- `alternate_coherent_cleanup(...)`: alternate coherent variant retained for
  restricted-subspace comparison.
- `swap_state_transfer_reference(...)`: direct SWAP-only transfer reference.

Tests compare both on the restricted input subspace `|psi,0,0>` and verify they
produce the same routed output there. This does not claim the full unitaries are
globally identical outside that subspace.

CI style gates currently cover the modular package surface (`circuits.py`,
`analysis.py`, `state_preparation.py`, `measurements.py`, `metrics.py`,
`validation.py`, tests, examples). The original monolithic core file remains
temporarily exempt pending decomposition migration.

### Completed

- Stage 1 fixed-input and branch-conditioned analysis.
- Fifth-wire theorem regression checks.
- Victim-subsystem invariance checks in the reconstructed branch model.
- Numerical validation and perturbation-bound reporting.

### Open / Explicitly Unresolved

- Exact Boolean acceptance condition implemented by the full original educational detector register.
- Hardware execution and noise-model validation.
- Malicious compiler prototype implementation.

## Detector Condition Note

The current script uses a provisional educational acceptance rule:

$$
\mathrm{accept} = (c \neq b) \lor (r_B = v)
$$

This rule is intentionally labeled provisional until the original educational circuit's exact detector register is fully reconstructed and matched.

## Documentation

- [PAPER.md](docs/PAPER.md)
- [RESEARCH_AGENDA.md](docs/RESEARCH_AGENDA.md)
- [THREAT_MODEL.md](docs/THREAT_MODEL.md)
- [TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md)
- [VALIDATION_FRAMEWORK.md](docs/VALIDATION_FRAMEWORK.md)
- [INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md)

## Research Draft 0.6 Artifacts

- PDF manuscript: [docs/paper/v0.6.0/Vi_Connelly_Known_State_Qubits_Research_Draft_v0_6.pdf](docs/paper/v0.6.0/Vi_Connelly_Known_State_Qubits_Research_Draft_v0_6.pdf)
- Full source package (release asset): [Vi_Connelly_Known_State_Qubits_Research_Package_v0_6.zip](https://github.com/redxe/quantum-reuse-security/releases/download/v0.6.0/Vi_Connelly_Known_State_Qubits_Research_Package_v0_6.zip)
- Standalone LaTeX entry file: [docs/paper/v0.6.0/source/main.tex](docs/paper/v0.6.0/source/main.tex)

Repository hygiene policy: keep manuscript source and PDF in Git, and publish
manuscript ZIP archives as release assets only.

## Citation

Use repository metadata in [CITATION.cff](CITATION.cff).

### Release Citation

Use the published release artifact for stable citation and review:

- [v0.6.0 Release](https://github.com/redxe/quantum-reuse-security/releases/tag/v0.6.0)

### BibTeX

```bibtex
@software{connelly2026_quantum_reuse_security,
  author = {Connelly, Vi},
  title = {Known-State Qubits as Both Resource and Risk},
  year = {2026},
  version = {0.6.0},
  url = {https://github.com/redxe/quantum-reuse-security}
}
```

## Author

Vi Connelly

## License

MIT License. See [LICENSE](LICENSE).

## Social Preview

Set the repository social preview image from GitHub settings:

`Settings -> General -> Social preview`
