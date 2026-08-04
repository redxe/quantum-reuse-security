# Fifth-Wire Branch-Conditioned Analysis

## Scope

This run analyzes the corrected advanced circuit after removing the redundant
second Alice measurement checkpoint. Alice's value `v`, basis `b`, Eve's basis
`e`, Eve's measurement result `r_E`, and Bob's basis `c` are treated explicitly.

Backend: **not installed; exact NumPy backend used**

The screenshot-specific advanced circuit corresponds to `e = 1`, because the
Eve-side signal receives a Hadamard immediately before measurement. The run also
includes `e = 0` to expose the complete BB84 information pattern.

## Routing result

The two SWAPs are:

1. `SWAP(q3,q4)`
2. `SWAP(q2,q4)`

They implement:

`(q2,q3,q4) -> (q3,q4,q2)`.

Therefore, after routing:

- `q2` carries the clean duplicate to Bob;
- `q3` is the clean workspace used for Bob's basis choice;
- `q4` carries Eve's post-measurement branch and is the candidate latch wire.

## Exact fifth-wire result

Conditioned on Eve's measurement result:

`rho_5^(v,b,e,r_E) = |r_E><r_E|`.

After averaging over Eve's outcome:

- If `e = b`, then `rho_5 = |v><v|`; the fifth wire reveals Alice's value
  perfectly.
- If `e != b`, then `rho_5 = I/2`; the fifth wire reveals no value information.
- With `v` known and `e` fixed, comparing the two basis choices has trace
  distance `1/2`, giving a 75% optimal single-shot basis guess.
- If Eve's basis is uniform and then forgotten, the fifth wire remains a noisy
  record of `v` with trace distance `1/2`, giving a 75% value guess, but it
  contains no distinguishable basis information.

## Information quantities

- Matching Eve/Alice basis: **1 bit** about `v`.
- Mismatched basis: **0 bits** about `v`.
- Uniform Eve basis, forgotten: **0.188722 bits**
  of mutual information about `v`.
- Uniform Eve basis retained as side information: **0.5 bits** about `v` per
  attacked transmission.
- Basis information when `v` is known and `e` is fixed:
  **0.311278 bits**.
- Holevo upper bound for the full pair `(v,b)` at fixed `e`: **0.5 bits**.

## Victim-side check

Across every fixed `(v,b,e,r_E)` branch:

- minimum victim-subsystem fidelity: **1.000000000000**
- maximum victim-subsystem trace distance: **1.233e-32**
- minimum provisional matched-basis acceptance probability: **1.000000000000**

Under this fixed-branch abstraction, Bob receives the independently prepared
duplicate exactly. Eve's measurement result is moved to `q4`, while the
legitimate `q0..q3` subsystem is unchanged relative to the clean routed
baseline.

## Claim boundary

This proves source-access leakage in the reconstructed abstract circuit. It does
not prove that a channel-only adversary can obtain the same information, and it
does not yet identify the book circuit's exact Boolean acceptance register.
The acceptance metric used here is provisional:

`accept = (c != b) OR (Bob_result == v)`.

## Generated files

- `branch_conditioned_results.csv`
- `averaged_fifth_wire_states.csv`
- `distinguishability_metrics.csv`
- `information_summary.json`
- `fifth_wire_bloch_z.png`
- `trace_distance_summary.png`
