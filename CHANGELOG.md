# Changelog

## 0.7.0 - 2026-08-04

- Issue #3: Moved all `run_analysis` orchestration out of
  `parameterized_fifth_wire_analysis.py` into `analysis.py`.
  The monolith is now a backward-compatibility facade only.
- Issue #2: Added Qiskit Statevector parity backend
  (`src/quantum_reuse/qiskit_backend.py`) with `build_protocol_circuit`,
  `enumerate_eve_branches_qiskit`, and `qiskit_available`.
  Added `run_analysis(backend="numpy"|"qiskit")` dispatcher and
  `--backend` CLI flag.  Added 43 parametric parity tests and 1
  end-to-end CSV artifact parity test.  Added `qiskit-parity` permanent
  CI gate (Qiskit 2.5.1).
- Bumped `qiskit` optional extra to `>=1.0.0,<3` (both `pyproject.toml`
  and `setup.py`).
- Added `__version__ = "0.7.0"` to package `__init__`.
- Added Backend Selection section to `docs/TECHNICAL_REFERENCE.md`
  (qubit mapping, simulation constraints, parity tolerance).
- Updated `README.md` with Qiskit backend in implemented list and
  quickstart.

## 0.6.0 - 2026-08-03

- Reconciled repository metadata with actual project state.
- Added modular package layout under src/quantum_reuse.
- Added CLI: python -m quantum_reuse analyze --output <dir>.
- Added fixed-input theorem summary command.
- Added tests covering branch probabilities, fifth-wire theorem, victim preservation, coherent cleanup identity, and validation checks.
- Added CI workflow for tests and deterministic output regression checks.
- Added pyproject.toml with editable-install and optional extras support.
- Added CITATION.cff.
- Added docs/TECHNICAL_REFERENCE.md.
- Updated author metadata to Vi Connelly.
