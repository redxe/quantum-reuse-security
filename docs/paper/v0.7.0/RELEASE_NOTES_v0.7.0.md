# Research Draft 0.7 release notes

Research Draft 0.7 adds a navigable security capability matrix and a complete evidence registry while preserving the existing deterministic analysis package.

## Added in 0.7

- Hyperlinked 5-by-6 attacker-access / information-target capability matrix.
- Thirty cell records with feasibility, limitation, workaround, mitigation, and evidence status.
- Color-independent symbols for demonstrated contributions, hypotheses, alternate routes, stronger-access assumptions, no-go boundaries, and mitigations.
- Highlighted D3 -> B2 -> B6 source-access / retained-branch / delayed-use contribution chain.
- Updated abstract, introduction, threat model, research agenda, conclusion, preface, reproducibility appendix, and bibliography.
- Reviewer-facing matrix preview image.
- Manuscript audit and PDF preflight records.

## Claim boundary

A star marks a contribution demonstrated by this artifact. It does not by itself assert world-first literature priority. The original educational detector semantics, Qiskit parity, compiler-pass prototype, and process-level victim-channel analysis remain open work.

## Build

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The resulting manuscript is `Vi_Connelly_Known_State_Qubits_Research_Draft_v0_7.pdf`.
