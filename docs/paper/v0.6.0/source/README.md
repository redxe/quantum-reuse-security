# Known-State Qubits as Both Resource and Risk - Research Draft 0.6

Author: Vi Connelly  
AI research, analysis, drafting, and reproducibility collaborator: GPT-5.6 Thinking (OpenAI)

This package contains the LaTeX manuscript, figures, data, and code snapshot for Research Draft 0.6.

Public repository: https://github.com/redxe/quantum-reuse-security

## Revision 0.6 additions

- Corrected Alice checkpoint circuits with the redundant repeated measurement removed.
- Semantic wire mapping through the ordered SWAP network.
- Fixed-input fifth-wire theorem and information metrics.
- Victim-subsystem branch comparison.
- Open research-software and continuous-integration section.
- Public roadmap issues for detector reconstruction, Qiskit parity, and core-module decomposition.
- Author metadata updated to Vi Connelly.

## Build

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```
