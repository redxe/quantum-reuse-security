---
name: Qiskit Parity Implementation
about: Add and verify a full Qiskit circuit implementation equivalent to the NumPy reference branch model
title: "qiskit: implement parity with numpy branch model"
labels: ["enhancement", "qiskit", "verification"]
assignees: []
---

## Objective
Implement a complete Qiskit-backed circuit path that matches the existing deterministic NumPy branch-conditioned reference model within stated tolerances.

## Current State
- Qiskit support exists as skeleton-level naming/API compatibility only.
- NumPy path is the canonical validated implementation.

## Deliverables
- Full Qiskit circuit construction path for the modeled protocol.
- Statevector or density-matrix extraction mapped to existing metric outputs.
- Cross-backend parity tests against NumPy reference for branch outputs and summary metrics.
- Clear backend selection/runtime documentation.

## Acceptance Criteria
- Running parity tests demonstrates agreement on key observables with explicit tolerance bounds.
- CLI behavior is deterministic for simulator-based Qiskit runs.
- Differences, if any, are documented and bounded (numerical ordering, floating-point effects, etc.).
- CI includes an optional or gated parity job if dependency cost is acceptable.

## Proposed Work Plan
1. Implement Qiskit circuit builder with explicit register/wire mapping.
2. Add conversion utilities from simulator outputs to existing data schema.
3. Create parity tests over all branch-conditioned cases and aggregate metrics.
4. Document limitations and reproducibility expectations.
5. Decide CI strategy (always-on matrix, optional extra, or nightly parity).

## Risks
- Backend/version drift in Qiskit can affect determinism and CI stability.
- Semantics mismatch in measurement/control flow may require staged reconciliation.

## Validation Checklist
- [ ] Branch-level parity tests pass.
- [ ] Aggregated metric parity tests pass.
- [ ] CLI/docs explain backend mode and expected reproducibility.
- [ ] CI strategy documented and implemented.
