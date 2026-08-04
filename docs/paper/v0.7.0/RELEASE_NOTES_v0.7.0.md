# Research Draft 0.7 release notes

Research Draft 0.7 adds a navigable security capability matrix, a complete evidence registry, a Qiskit Statevector parity backend, a formalized privilege vocabulary, and parametric victim-channel verification beyond the four BB84 inputs.

## Added in 0.7

- Hyperlinked 5-by-6 attacker-access / information-target capability matrix.
- Thirty cell records with feasibility, limitation, workaround, mitigation, and evidence status.
- Color-independent symbols for demonstrated contributions, hypotheses, alternate routes, stronger-access assumptions, no-go boundaries, and mitigations.
- Highlighted D3 -> B2 -> B6 source-access / retained-branch / delayed-use contribution chain.
- Updated abstract, introduction, threat model, research agenda, conclusion, preface, reproducibility appendix, and bibliography.
- **Qiskit Statevector backend** (`qiskit_backend.py`): exhaustive fixed-input parity (43 cases + 1 end-to-end CSV comparison) and a sampled continuous-state check (8 pure states × 2 Eve bases, seed 7); permanent `qiskit-parity` CI gate.
- **Module decomposition** (Issue #3): `run_analysis` and all orchestration moved to `analysis.py`; `parameterized_fifth_wire_analysis.py` is now a backward-compatibility facade.
- **Privilege vocabulary** (Issue #5): use, read, retain, and export defined with non-implication counterexamples; integrated into threat model chapter and capability matrix cell labels.
- **Parametric victim-channel preservation** (Issue #7): 60-setting structured angular grid (108 realized branches) and 200-sample deterministic sweep (400 settings, 800 branches) verify victim fidelity ≥ 1−4×10⁻¹⁶ and trace distance ≤ 8.6×10⁻¹⁶ across 908 total branches from 460 parameter settings; Qiskit cross-check on 16 parameter settings. Counts committed to `data/parametric_victim_summary.json`.
- Scientific scope note in threat model: parametric numerical evidence is not a formal Choi-state channel theorem.

## Claim boundary

A star marks a contribution demonstrated by this artifact. It does not by itself assert world-first literature priority. The exact educational detector acceptance register, complete branch-level Qiskit parity, and hardware validation remain explicit open problems.

## Build

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

The resulting manuscript is `Vi_Connelly_Known_State_Qubits_Research_Draft_v0_7.pdf`.
