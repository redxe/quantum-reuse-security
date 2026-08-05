# Known-State Qubits as Both Resource and Risk - Research Draft 0.7

Author: Vi Connelly  
AI research, analysis, drafting, and reproducibility collaborator: GPT-5.6 Thinking (OpenAI)

This package contains the LaTeX manuscript, figures, data, and code snapshot for Research Draft 0.7.

Public repository: https://github.com/redxe/quantum-reuse-security

## Revision 0.7 additions

- Corrected Alice checkpoint circuits with the redundant repeated measurement removed.
- Semantic wire mapping through the ordered SWAP network.
- Fixed-input fifth-wire theorem and information metrics.
- Victim-subsystem branch comparison.
- Open research-software and continuous-integration section.
- Public roadmap issues for detector reconstruction, Qiskit parity, and core-module decomposition.
- Author metadata updated to Vi Connelly.
- Hyperlinked 5-by-6 security capability matrix with a complete cell registry.
- Color-and-symbol legend that distinguishes feasibility, no-go boundaries, alternatives, mitigations, and project contributions.
- **Qiskit Statevector parity backend** (`qiskit_backend.py`) with permanent `qiskit-parity` CI gate; exhaustive fixed-input parity (43 cases + 1 end-to-end CSV), plus a sampled continuous-state check (8 states × 2 Eve bases).
- **Monolith decomposition** (Issue #3): analysis orchestration moved to `analysis.py`; legacy facade retained for backward compatibility.
- **Privilege vocabulary** (Issue #5): use/read/retain/export framework formalized in threat model chapter.
- **Parametric victim-channel preservation** (Issue #7): 60-sample grid + 200-sample random sweep confirm preservation beyond BB84 inputs, cross-validated with Qiskit.
- Scientific scope note: parametric sweep is numerical evidence, not a formal channel theorem; Choi-state test is noted as a future follow-up.

## Build

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

## Release-integrity policy

`MANIFEST.txt` is the curated inventory for the complete release package. It
includes the PDF and plot assets that continuous integration generates from the
committed manuscript sources, scripts, and data. The generated PDF is uploaded
as a CI artifact and preflighted structurally; it is not compared byte-for-byte
because the TeX build does not yet control timestamps and PDF metadata.

`SHA256SUMS.txt` covers every committed immutable package file except itself,
using the repository's canonical line endings. Generated PDF and image assets
are validated by the clean CI build and manifest check rather than treated as
committed checksum inputs.
