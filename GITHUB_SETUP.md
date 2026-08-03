# GITHUB_SETUP.md - Next Steps for Publishing

## What's Ready

✅ **Project structure organized:**
- `src/` — Ready for main analysis script (move from root)
- `data/` — Ready for CSV and JSON data files  
- `docs/` — Comprehensive documentation (5 files)
- `examples/` — Ready for example scripts
- `.gitignore` — Excludes .venv, run_output, __pycache__

✅ **Professional documentation:**
- README.md with paper abstract, findings, and reproduction steps
- PAPER.md — Research summary with 5 main claims
- THREAT_MODEL.md — Attack vectors and 4 defense mechanisms
- RESEARCH_AGENDA.md — 4-stage publication plan
- VALIDATION_FRAMEWORK.md — Numerical methods and error analysis
- INTERVIEW_GUIDE.md — Portfolio and interview preparation

✅ **Metadata files:**
- LICENSE (MIT)
- requirements.txt (numpy, pandas, matplotlib)
- setup.py (package configuration)

---

## Steps to Publish on GitHub

### 1. Organize Files into Directories

Move existing files to proper locations:

```bash
# Move script to src/
mv parameterized_fifth_wire_analysis.py src/quantum_reuse/

# Move data files to data/
mv *.csv data/
mv *.json data/
# Keep corrected_quirk_circuits.json in data/ for reference

# Move old documentation to archive/ (optional)
mkdir archive/
mv CODE_CHANGES_REFERENCE.md COMPLETION_SUMMARY.md DOCUMENTATION_INDEX.md \
   NUMERICAL_VALIDATION_SUMMARY.md PORTFOLIO_INTERVIEW_GUIDE.md \
   QUICK_REFERENCE.md README_VALIDATION_ENHANCEMENT.md VALIDATION_TECHNICAL_REFERENCE.md \
   archive/

# Keep run_report.md if it's the current output, or delete if regenerated
```

### 2. Generate Fresh Output

Run the analysis script once to generate clean `run_output/` directory:

```bash
# From project root
python src/quantum_reuse/parameterized_fifth_wire_analysis.py

# This will create:
# run_output/numerical_validation.json
# run_output/run_report.md
# run_output/branch_conditioned_results.csv
# run_output/averaged_fifth_wire_states.csv
# run_output/distinguishability_metrics.csv
```

### 3. Create Repository on GitHub

```bash
# Initialize git
git init

# Add all files
git add .

# Verify .gitignore is working
git status
# Should NOT show: .venv/, __pycache__/, run_output/, *.pyc

# First commit
git commit -m "Initial commit: Quantum compiler security research

- Novel threat model: malicious qubit reuse via compiler
- Coherent teleportation theorem + case study
- Numerical validation framework (4 levels, machine-epsilon precision)
- Comprehensive documentation and research roadmap
- Stage 1 complete: semantic wire mapping and fixed-input tests
- Stages 2-4 planned: information metrics, compiler prototype, hardware validation"

# Add remote and push
git remote add origin https://github.com/yourusername/quantum-reuse-security.git
git branch -M main
git push -u origin main
```

### 4. GitHub Repository Settings

- **Description:** "Quantum compiler security: hidden information leakage through qubit reuse"
- **Topics:** `quantum-computing`, `quantum-security`, `quantum-information-theory`, `compiler-security`, `numerical-validation`
- **License:** MIT (already in repo)
- **README:** Will auto-display README.md

### 5. Optional Enhancements

#### Add CITATION.cff (for researchers)
```yaml
cff-version: 1.2.0
message: "If you use this software, please cite it as below."
authors:
  - family-names: "Connelly"
    given-names: "Levi"
type: software
title: "Known-State Qubits as Both Resource and Risk"
version: 0.5.0
date-released: 2026-08-03
url: "https://github.com/yourusername/quantum-reuse-security"
license: "MIT"
```

#### Add .github/workflows/ci.yml (Continuous Integration)
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/
```

#### Add CONTRIBUTING.md
```markdown
# Contributing

This is a research project. Contributions welcome!

## Areas of Interest
- Stage 2: Information-theoretic metrics (Holevo information, mutual information)
- Stage 3: Malicious compiler prototype
- Stage 4: Hardware validation on IBM/IonQ/Rigetti devices
- Documentation improvements

## Code Standards
- Python 3.8+
- NumPy for all linear algebra
- Docstrings for all functions
- Type hints encouraged

## Reporting Issues
- Use GitHub issues for bugs, questions, or suggestions
- For security issues, email author directly (ltconnelly314@gmail.com)
```

#### Add CHANGELOG.md
```markdown
# Changelog

## [0.5.0] - 2026-08-03

### Added
- Coherent teleportation theorem (Claim 1)
- Educational spy-detector case study (Claim 2)
- Four-level equivalence hierarchy (E0-E3)
- Numerical validation framework (4 levels)
- Malicious qubit-reuse threat model
- Four defense mechanisms (ranked)
- Comprehensive documentation (5 markdown files)
- Research roadmap (Stages 1-4)
- Portfolio interview guide

### Status
- Stage 1 (Semantic Wire Mapping): Complete
- Stages 2-4: Planned
```

---

## Recommended Submission Venues

### Tier 1 (High Impact, Competitive)
- **ACM CCS 2027** — Computer and Communications Security (security focus)
- **IEEE TQE** — IEEE Transactions on Quantum Engineering (hardware/systems focus)

### Tier 2 (Specialized, Good Fit)
- **Quantum Information Processing** (journal, theory focus)
- **QIP 2027** (Quantum Information Processing, preprint/invited talks)

### Tier 3 (Visibility, Preprint First)
- **arXiv.org** (quantum-ph, cs.CR sections) — post immediately for priority
- **GitHub + preprint** — establish priority, gather feedback

---

## Before Publishing: Final Checklist

- [ ] Run code once to generate fresh output
- [ ] Update all file paths in documentation (e.g., "data/results/" instead of root)
- [ ] Verify .gitignore excludes .venv and run_output/
- [ ] Test README reproduction steps
- [ ] Spell-check all markdown files
- [ ] Verify all LaTeX equations render correctly
- [ ] Create GitHub repository
- [ ] Push initial commit
- [ ] Add GitHub topics and description
- [ ] (Optional) Set up CI/CD with GitHub Actions
- [ ] Post announcement on arXiv (if targeting academic audience)
- [ ] Share in quantum computing communities (Reddit, Qiskit slack, etc.)

---

## Long-Term Maintenance

### Expected Questions
- How to run specific experiments → [RESEARCH_AGENDA.md](docs/RESEARCH_AGENDA.md)
- How to understand numerical validation → [VALIDATION_FRAMEWORK.md](docs/VALIDATION_FRAMEWORK.md)
- What's the threat model → [THREAT_MODEL.md](docs/THREAT_MODEL.md)
- Career/interview info → [INTERVIEW_GUIDE.md](docs/INTERVIEW_GUIDE.md)

### Future Work (Stages 2-4)
- Stage 2 branches: `branch/stage2-information-metrics`
- Stage 3 branches: `branch/stage3-compiler-prototype`
- Stage 4 branches: `branch/stage4-hardware-validation`

### Releases
- v0.5.0 (current): Stage 1 complete, theory validated
- v1.0.0 (target): Stage 2 complete, information metrics published
- v1.5.0 (target): Stage 3 complete, compiler prototype working
- v2.0.0 (target): Stage 4 complete, hardware results analyzed

---

## Questions?

See [README.md](../README.md) for quick start, or [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md) for common technical questions.
