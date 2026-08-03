# Known-State Qubits as Both Resource and Risk

**Coherent Cleanup, Qubit Reuse, and Stealthy Information Leakage in Quantum Circuits**

A computational study and numerical validation framework for analyzing qubit reuse safety, information flow, and hidden state correlations in quantum circuits.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.48550%2FarXiv.2408.xxxxx-red.svg)](https://arxiv.org/)

## Overview

This repository contains the complete analysis, reproducible code, and numerical validation framework for the research paper:

> **Known-State Qubits as Both Resource and Risk: Coherent Cleanup, Qubit Reuse, and Stealthy Information Leakage in Quantum Circuits**
>
> Levi Connelly and GPT-5.6 Thinking (OpenAI)  
> Research Draft 0.5 — August 2026

### Key Findings

The paper demonstrates that qubits safe for reuse require more than a known computational-basis state. It proves that:

1. **Coherent Teleportation Cleanup**: A five-qubit circuit with two final Hadamards provably maps $|\psi 00\rangle$ to $|00\psi\rangle$ while preserving entanglement with arbitrary reference systems.

2. **Hidden Information Leakage**: An educational spy-detector circuit can restore the baseline computational-basis probability distribution (total-variation distance: $8.90 \times 10^{-9}$) while leaving purity reduced from 1 to 1/2 and fidelity at 0.4268.

3. **Information-Disturbance Boundary**: Orthogonal classical information can be copied into hidden workspace without changing its source. Nonorthogonal pure states cannot reveal distinguishable information without physical trace.

4. **Four Levels of Equivalence**: Matching histograms (E0) ≠ Matching reduced states (E1) ≠ Process equivalence (E2) ≠ Full execution fidelity (E3).

5. **Malicious Reuse Threat Model**: Reclaimed qubits present an attractive attack surface for privileged compilers, runtimes, or control stacks seeking hidden workspace.

## Repository Structure

```
.
├── README.md                          # This file
├── LICENSE                            # MIT License
├── CITATION.cff                       # Citation metadata
├── .gitignore                         # Git ignore rules
├── requirements.txt                   # Python dependencies
├── setup.py                           # Package setup
│
├── src/
│   └── quantum_reuse/
│       ├── __init__.py
│       ├── simulate.py                # Main simulation
│       ├── validation.py              # Numerical validation framework
│       └── circuits.py                # Circuit definitions
│
├── data/
│   ├── quirk_exports/                 # Supplied Quirk column arrays
│   ├── results/                       # Simulation outputs
│   ├── baseline_export.json           # Baseline circuit amplitudes (32)
│   ├── intercept_resend_export.json   # Intercept-resend amplitudes (32)
│   └── advanced_export.json           # Advanced source-access amplitudes (32)
│
├── docs/
│   ├── PAPER.md                       # Paper summary & main claims
│   ├── RESEARCH_AGENDA.md             # Four-stage research plan
│   ├── THREAT_MODEL.md                # Malicious reuse threat model
│   ├── TECHNICAL_REFERENCE.md         # Mathematical details
│   ├── VALIDATION_FRAMEWORK.md        # Numerical validation methods
│   └── INTERVIEW_GUIDE.md             # Portfolio & interview preparation
│
├── examples/
│   ├── coherent_teleportation.py      # Teleportation cleanup demo
│   ├── spy_detector_analysis.py       # Spy circuit exact analysis
│   └── information_leakage.py         # Hidden correlation example
│
└── tests/
    ├── test_teleportation.py          # Teleportation verification
    └── test_validation.py             # Validation framework tests
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/quantum-reuse-security.git
cd quantum-reuse-security

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Analysis

```bash
# Execute complete spy-detector analysis with numerical validation
python src/quantum_reuse/simulate.py

# Output files:
# - data/results/numerical_validation.json      (validation metrics)
# - data/results/run_report.md                  (analysis summary)
# - data/results/branch_conditioned_results.csv (detailed results)
```

### Run Examples

```bash
# Coherent teleportation cleanup demonstration
python examples/coherent_teleportation.py

# Spy-detector circuit analysis
python examples/spy_detector_analysis.py

# Information leakage analysis
python examples/information_leakage.py
```

## Core Results

### Case Study I: Coherent Teleportation

**Theorem (Coherent Teleportation Cleanup):**

For every single-qubit state $|\psi\rangle$:
$$U_{\text{clean}} |\psi\rangle_S|0\rangle_A |0\rangle_B = |0\rangle_S|0\rangle_A |\psi\rangle_B$$

**Implementation:** `src/quantum_reuse/circuits.py::coherent_teleportation()`

**Verification:** 
- 10,000 random states tested
- Maximum statevector error: $4.45 \times 10^{-16}$
- Minimum fidelity: $> 1 - 1.8 \times 10^{-15}$

### Case Study II: Educational Spy Detector

**Finding:** Advanced circuit restores baseline Z-basis histogram (TVD: $8.90 \times 10^{-9}$) but:
- Purity: $1 \to 1/2$
- Fidelity with baseline: $0.4268$
- Trace distance from baseline: $0.6184$

**Interpretation:** Stealthy at E0 (histogram level), but fails E1 (reduced-state level).

| Metric | Baseline | Intercept–Resend | Advanced |
|--------|----------|------------------|----------|
| Purity | 1.0000 | 0.5000 | 0.5000 |
| Fidelity | 1.0 | 0.25 | 0.4268 |
| Trace Distance | 0 | 0.8090 | 0.6184 |
| Z-TVD | 0 | 0.3750 | $8.90 \times 10^{-9}$ |

## Numerical Validation

All computed density matrices undergo rigorous validation:

✅ **Trace preservation**: $|\text{Tr}(\rho) - 1| < 10^{-10}$  
✅ **Hermiticity**: $||\rho - \rho†|| < 10^{-14}$  
✅ **Positive semi-definite**: $\lambda_{\min} > -10^{-14}$  
✅ **Error-to-epsilon ratio**: $1.00\times$ machine epsilon (optimal)

See [VALIDATION_FRAMEWORK.md](docs/VALIDATION_FRAMEWORK.md) for complete methodology.

## Research Agenda

Four-stage plan for publication:

### Stage 1: Semantic Wire Mapping & Fixed-Input Tests
Map each wire's semantic role through SWAP permutations; compute victim and attacker density matrices for each $(v,b) \in \{0,1\}^2$.

### Stage 2: Attacker-Information Metrics
Measure Holevo information $\chi(X : E)$, mutual information, and phase-sensitive observables.

### Stage 3: Malicious Compiler Prototype
Implement controlled research prototype with qubit-liveness analysis and defense evaluation.

### Stage 4: Hardware & Noise
Compare coherent cleanup, measurement-reset, and fresh allocation on real devices.

See [RESEARCH_AGENDA.md](docs/RESEARCH_AGENDA.md) for full details.

## Threat Model

**Adversary Capabilities:**
- Modifying compiler optimization passes
- Altering runtime qubit-liveness decisions
- Inserting gates after user inspection
- Modifying pulse-level implementations
- Accessing source-preparation controls
- Allocating undocumented physical qubits

**Attack Pattern:**
1. Find workspace (clean/reclaimed qubits)
2. Select secret-dependent signal (basis labels, key-dependent branches)
3. Couple reversibly (CNOT, Toffoli, controlled rotations)
4. Preserve checked output (avoid victim path, exploit restricted measurements)
5. Extract (measure attacker register, route to unauthorized output)

See [THREAT_MODEL.md](docs/THREAT_MODEL.md) for formal definitions.

## Defense Mechanisms

- **State-and-secrecy contracts**: Extend state assertions to security assertions
- **Complementary-basis testing**: Randomized tests in non-computational bases
- **Cross-layer attestation**: Bind circuit, mapping, timing, and pulse layers
- **Trap and canary circuits**: Interleave circuits to detect unauthorized coupling
- **Isolation and least privilege**: Compartmentalize secrets and control channels

## Files & Reproducibility

### Supplied Data
- `data/baseline_export.json` — Baseline circuit 32 amplitudes
- `data/intercept_resend_export.json` — Intercept-resend 32 amplitudes
- `data/advanced_export.json` — Advanced source-access 32 amplitudes

### Generated Results
- `data/results/numerical_validation.json` — Validation metrics
- `data/results/branch_conditioned_results.csv` — Per-branch analysis (12 branches × 2 bases)
- `data/results/averaged_fifth_wire_states.csv` — Averaged fifth-wire states
- `data/results/distinguishability_metrics.csv` — Trace distance & mutual information

### Reproducibility
All numerical results are deterministic. To regenerate:
```bash
python src/quantum_reuse/simulate.py --output data/results/
```

## Citation

**APA Format:**
```
Connelly, L., & OpenAI GPT-5.6 Thinking. (2026). Known-state qubits as both 
resource and risk: Coherent cleanup, qubit reuse, and stealthy information 
leakage in quantum circuits. Research Draft 0.5.
```

**BibTeX:**
```bibtex
@article{connelly2026qubits,
  title={Known-State Qubits as Both Resource and Risk},
  subtitle={Coherent Cleanup, Qubit Reuse, and Stealthy Information Leakage},
  author={Connelly, Levi and OpenAI},
  year={2026},
  month={August},
  version={Draft 0.5},
  note={arXiv preprint}
}
```

## Dependencies

- **Python** 3.8+
- **NumPy** ≥ 1.19.0 — Numerical linear algebra
- **Pandas** ≥ 1.1.0 — Data analysis
- **Matplotlib** ≥ 3.3.0 — Visualization
- **Qiskit** ≥ 0.25.0 (optional) — Quantum circuit construction

### Install all dependencies:
```bash
pip install -r requirements.txt
```

## Documentation

| Document | Purpose |
|----------|---------|
| [PAPER.md](docs/PAPER.md) | Research paper summary & main claims |
| [TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md) | Mathematical background & detailed proofs |
| [VALIDATION_FRAMEWORK.md](docs/VALIDATION_FRAMEWORK.md) | Numerical validation methodology |
| [RESEARCH_AGENDA.md](docs/RESEARCH_AGENDA.md) | Four-stage research plan |
| [THREAT_MODEL.md](docs/THREAT_MODEL.md) | Malicious-reuse threat model |
| [INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md) | Portfolio & interview prep |

## Key References

- Bennett et al. (1993). "Teleporting an Unknown Quantum State via Dual Classical and Einstein–Podolsky–Rosen Channels"
- Nielsen & Chuang (2010). *Quantum Computation and Quantum Information*
- Fuchs (1996). "Information Gain versus State Disturbance in Quantum Theory"
- Koashi & Imoto (2002). "Operations That Do Not Disturb Partially Known Quantum States"
- DeCross et al. (2023). "Qubit-Reuse Compilation with Mid-Circuit Measurement and Reset"

See full references in the paper.

## Limitations & Responsible Interpretation

**What this paper does NOT establish:**
- Novelty of coherent measurement deferral or teleportation cleanup
- Attack on BB84 under standard channel-only threat model
- Demonstrated malware on production quantum hardware
- Universal decryption or exploitation of encrypted data
- Specific recovery of protected variables from fifth-wire correlations

**What it DOES establish:**
- Exact coherent cleanup identity with formal proof
- Source-access security case study with computed metrics
- General information-disturbance boundary theorem
- Concrete research program for secure qubit reuse

## Contributing

This is a research draft. Contributions are welcome:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/analysis`)
3. Commit your changes (`git commit -am 'Add analysis'`)
4. Push to the branch (`git push origin feature/analysis`)
5. Open a Pull Request

## License

MIT License — See [LICENSE](LICENSE) for details.

## Authors

**Levi Connelly**  
Independent Researcher, Anderson, Indiana, USA  
ltconnelly314@gmail.com

**GPT-5.6 Thinking (OpenAI)**  
AI research, analysis, drafting, and reproducibility collaborator  

The AI collaborator provided substantial assistance in mathematical exposition, source-code generation, LaTeX implementation, numerical consistency checks, figure design, reference auditing, and manuscript revision. Levi Connelly supplied the original observations, circuit exports, research questions, interpretive corrections, and motivating security hypothesis.

The human author retains responsibility for all claims and future submissions.

## Status

- **Current Version:** Research Draft 0.5
- **Last Updated:** August 3, 2026
- **Submission Status:** Questions required before journal submission (see Appendix C in paper)

## Contact & Questions

For questions about:
- **Mathematical content:** See [TECHNICAL_REFERENCE.md](docs/TECHNICAL_REFERENCE.md)
- **Reproducibility:** See [Reproducibility](#files--reproducibility) section
- **Implementation details:** See docstrings in `src/quantum_reuse/`
- **Research direction:** See [RESEARCH_AGENDA.md](docs/RESEARCH_AGENDA.md)

---

**Disclaimer:** This work demonstrates potential information channels in quantum circuits under source-access threat models. It does not prove attacks on deployed quantum systems or claims to break existing cryptographic protocols. Quantum mechanics is not violated. The research explores compiler and software security boundaries in quantum computing.
