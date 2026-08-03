# Threat Model

## Model

Adversary has privileged compiler/runtime control and can inject operations into reclaimed qubits while attempting to preserve user-visible histogram behavior.

## Implemented Evidence in This Repository

- Deterministic branch-conditioned analysis over fixed $(v,b,e,r_E)$ settings.
- Verified fifth-wire leakage theorem:
  - matching basis ($e=b$): fifth wire reveals Alice value;
  - mismatched basis ($e\neq b$): fifth wire is maximally mixed.
- Victim-subsystem preservation in the reconstructed branch model within floating-point precision.

## Attack Workflow

1. Locate reclaimable workspace qubits.
2. Couple attacker-controlled operations to branch-dependent signals.
3. Preserve checked outputs where possible.
4. Extract side information from attacker register.

## Constraints

- Cannot violate quantum mechanics.
- Nonorthogonal information extraction without disturbance remains bounded.
- Claims are source-access model claims, not channel-only BB84 breaks.

## Detector Gap (Open)

Current acceptance expression in code is provisional:

$$
\mathrm{accept}=(c\neq b)\lor(r_B=v).
$$

The exact educational detector register still must be reconstructed to replace this provisional metric with the original Boolean detector behavior.

## Defensive Directions

- Cross-layer attestation of circuit-to-pulse path.
- Complementary-basis and trap-based checks.
- State-and-secrecy contracts for reuse boundaries.
- Least-privilege runtime design around qubit allocation and measurement routing.
