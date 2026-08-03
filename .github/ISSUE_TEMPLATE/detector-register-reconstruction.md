---
name: Detector Register Reconstruction
about: Reconstruct and validate the exact detector acceptance register from the original educational circuit
title: "detector: reconstruct exact acceptance register"
labels: ["research", "detector", "high-priority"]
assignees: []
---

## Objective
Replace the provisional acceptance rule with the exact Boolean acceptance condition implemented by the original educational detector register.

## Current State
- The repository currently documents a provisional rule in README and run reports.
- Stage 1 deterministic branch-conditioned analysis is validated, but detector logic remains an explicit gap.

## Deliverables
- Reconstructed detector-register logic with explicit wire/bit semantics.
- Traceable mapping from original circuit operations to code.
- Updated deterministic outputs and theorem-side interpretations if needed.
- Tests that fail under the provisional rule and pass under the reconstructed rule.
- Documentation update that removes or narrows provisional wording.

## Acceptance Criteria
- A formal truth table for detector acceptance is included in docs.
- Code path used by `python -m quantum_reuse analyze --output <dir>` executes reconstructed logic.
- CI passes with deterministic regression checks after baseline updates (if expected changes occur).
- README and technical docs describe final detector condition without ambiguity.

## Proposed Work Plan
1. Identify canonical original detector-register circuit and encode gate-by-gate semantics.
2. Derive and verify the acceptance Boolean condition symbolically and numerically.
3. Implement condition in analysis path with tests for all branch combinations.
4. Regenerate deterministic artifacts and quantify deltas vs prior provisional outputs.
5. Update docs and changelog notes with reconciliation details.

## Risks
- Ambiguity in source circuit interpretation may create multiple candidate conditions.
- Regression deltas may alter prior narrative claims unless carefully bounded.

## Validation Checklist
- [ ] Unit tests cover all relevant detector branch cases.
- [ ] Regression tests compare old vs new outputs and summarize deltas.
- [ ] Documentation updated in README and docs/TECHNICAL_REFERENCE.md.
- [ ] Changelog entry added for behavior change.
