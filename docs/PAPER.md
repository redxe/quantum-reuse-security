# Known-State Qubits as Both Resource and Risk: Paper Summary

## Scope

This repository currently provides deterministic software evidence for a source-access threat model in a modified educational spy-detector circuit. It is not a hardware attack demonstration.

## Implemented and Reproducible Results

### 1) Fixed-Input Fifth-Wire Theorem (Completed)

For fixed Alice value $v$, Alice basis $b$, and Eve basis $e$, the averaged fifth-wire reduced state satisfies:

$$
\rho_5^{(v,b,e)}=
\begin{cases}
|v\rangle\langle v|,& e=b,\\
I/2,& e\neq b.
\end{cases}
$$

This is implemented in the deterministic branch-conditioned analysis and covered by regression tests.

### 2) Victim-Subsystem Preservation in the Reconstructed Branch Model

For each fixed branch $(v,b,e,r_E)$, the victim subsystem is preserved relative to the clean routed baseline within floating-point precision.

### 3) Numerical Validation

All computed reduced states are validated for:

- trace normalization;
- Hermiticity;
- positive semidefinite spectrum;
- perturbation-scale sanity against machine epsilon.

### 4) Source-Access Threat Claim Boundary

These results support source-access leakage claims in the reconstructed branch-conditioned model. They do not claim a channel-only BB84 break or production hardware exploitation.

## Detector Condition Status

The currently reported acceptance rule remains explicitly provisional:

$$
\mathrm{accept}=(c\neq b)\lor(r_B=v).
$$

A next-step task is to reconstruct the original educational detector register exactly and compare that detector output directly against the advanced circuit.

## Stage Status

- Stage 1 fixed-input and branch-conditioned analysis: complete.
- Stage 2 information-metric expansion: next.
- Stage 3 malicious compiler prototype: planned.
- Stage 4 hardware/noise validation: planned.

## Repository Entry Points

- CLI analysis: `python -m quantum_reuse analyze --output run_output`
- Theorem summary: `python -m quantum_reuse fixed-input-summary`

## References

- Bennett et al. (1993), teleportation foundations
- Nielsen & Chuang (2010), quantum information fundamentals
- Fuchs (1996), information gain vs disturbance
- Koashi & Imoto (2002), non-disturbing operations on partially known states
