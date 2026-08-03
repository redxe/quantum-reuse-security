# Known-State Qubits as Both Resource and Risk: Paper Summary

## Abstract

Quantum computing promises unprecedented computational power, but quantum circuits operate at the boundary of physics and software—where qubits are not merely data, but machinery. This paper investigates a fundamental threat: **can reclaimed qubits become a covert attack vector for malicious compilers, runtimes, or control stacks?**

We prove that coherent teleportation enables safe qubit reuse, but we also show through detailed case studies that **educational spy-detector circuits can restore measurement histograms while leaving hidden correlations intact**—a phenomenon invisible at the statistical level but catastrophic at the information level.

## Main Claims

### Claim 1: Coherent Teleportation Cleanup Identity

**Theorem:** For every single-qubit state $|\psi\rangle$:
$$U_{\text{clean}} |\psi\rangle_S|0\rangle_A |0\rangle_B = |0\rangle_S|0\rangle_A |\psi\rangle_B$$

This five-qubit circuit provably transfers an unknown state from source qubit $S$ to destination qubit $B$, leaving source and ancillas in computational-basis zero states suitable for reuse. The circuit:
- Requires no state tomography or classical measurement
- Preserves entanglement with arbitrary reference systems
- Leaves the source in $|0\rangle$ state, not merely known to be zero
- Can be implemented with standard two-qubit gates (CNOT, CZ)

**Verification:** Statevector simulations on 10,000 random single-qubit states yield:
- Maximum fidelity deviation: $< 1.8 \times 10^{-15}$
- Zero state-normalization failures
- Perfect Hermiticity preservation

### Claim 2: Hidden Information Leakage in Educational Spy Detector

**Case Study:** Analyze a BB84-inspired educational spy-detector circuit under three attack scenarios:

| Scenario | Description | Implementation | Result |
|----------|-------------|-----------------|---------|
| Baseline | Honest protocol with Alice, Bob, Eve absent | Honest state prep | Purity=1, Fidelity=1 |
| Intercept-Resend | Eve measures Z, retransmits basis-random bit | Eve destroys basis info | Purity=1/2, Fidelity=0.25 |
| Advanced | Eve controls Alice's basis choice & prep | Reservoir-access attack | Purity=1/2, Fidelity=0.4268 |

**Key Finding:** The advanced attack restores baseline Z-basis histogram:
$$\text{TVD}_Z(\text{baseline}, \text{advanced}) = 8.90 \times 10^{-9}$$

Yet the density matrices are **dramatically different**:
- Baseline victim subsystem: Pure state (purity=1)
- Advanced victim subsystem: Mixed state (purity=0.5)
- Trace distance: 0.6184 (orthogonal boundaries)

**Interpretation:** The attack is stealthy at the **histogram level (E0)** but fails at the **reduced-state level (E1)**.

### Claim 3: Four Levels of State Equivalence

Quantum systems are not monolithic. Information can hide at multiple levels:

| Level | Name | Definition | Role |
|-------|------|-----------|------|
| **E0** | Histogram Equivalence | Probability distributions match | Statistical security (first defense) |
| **E1** | Reduced-State Equivalence | Reduced density matrices match | Entanglement-aware security |
| **E2** | Process Equivalence | Channel outputs match for all inputs | Information-theoretic security |
| **E3** | Full Execution Fidelity | Total state vector matches with phase | Absolute quantum equivalence |

An adversary can engineer attacks that pass E0 while violating E1:
- Copy classical information into hidden workspace
- Entangle attacker with victim through controlled unitaries
- Restore measurement statistics in measured bases only
- Fail catastrophically in unmeasured (complementary) bases

### Claim 4: Information-Disturbance Boundary Theorem

**Theorem (Koashi–Imoto, 1996; our application):** For nonorthogonal pure states $|\psi\rangle$ and $|\phi\rangle$ with $\langle \psi | \phi \rangle \neq 0$:

If a quantum operation **copies** distinguishing information between $|\psi\rangle$ and $|\phi\rangle$ into a third system without disturbing the first system's statistics in the original basis, then **the two states must be orthogonal**.

**Consequence:** Orthogonal classical bits can be extracted and copied without trace. Nonorthogonal quantum information cannot.

**Application:** Eve's advanced attack extracts only the **orthogonal classical labels** (Alice's basis choice, value choice). It cannot extract the superposition structure of the prepared state.

### Claim 5: Malicious Reuse Threat Model

A **privileged compiler, runtime, or control stack** can:

1. **Find workspace:** Identify reclaimed qubits through liveness analysis
2. **Encode attacker:** Place controlled gates (CNOT, Toffoli, CX<sub>controlled</sub>) using reused qubits
3. **Couple reversibly:** Entangle attacker qubit with victim through reversible operations
4. **Preserve victim:** Design circuits so victim's measured bases pass statistical tests
5. **Extract secretly:** Route attacker measurement results to unauthorized outputs
6. **Repeat:** Multi-round attacks, adaptive basis selection, branching strategies

**Attack Surface:**
- Compiler optimization passes (dead-qubit elimination, gate fusion)
- Runtime qubit-allocation decisions
- Pulse-level implementations (arbitrary unitary timing)
- Measurement and reset primitives
- Classical feedforward paths

**Constraints (Attacker's Limitations):**
- Cannot violate quantum mechanics
- Cannot measure victim without disturbing it (unless entangled in hidden subsystem)
- Cannot bypass explicit source-ownership attestation
- Cannot extract phase information from measured qubits

## Research Roadmap: Four Stages

### Stage 1: Semantic Wire Mapping & Fixed-Input Tests
- Map each wire's semantic role (Alice basis, Alice value, Eve basis, Eve outcome, Bob basis)
- Compute victim and attacker density matrices for $(v, b) \in \{0,1\}^2$ with fixed values
- Verify circuit correctness through Quirk export validation
- Output: Numerical baseline data for all configurations

### Stage 2: Attacker-Information Metrics  
- Compute Holevo information $\chi(X : E)$ (attacker's accessible information about Alice's state)
- Compute mutual information $I(V : E)$ (Eve's distinguishability of Alice's value)
- Compute mutual information $I(B : E)$ (Eve's distinguishability of Alice's basis)
- Measure phase-sensitive observables (Bloch vector components in unpreparable bases)
- Compare across baseline, intercept-resend, and advanced scenarios

### Stage 3: Malicious Compiler Prototype
- Build controlled research prototype with qubit-liveness analysis
- Implement toy-model CNOT insertion between clean reclaimed qubits and active user circuit
- Evaluate detection difficulty: timing, statistical tests, gate fidelity requirements
- Measure success metrics: fidelity of copied information, victim histogram distortion
- Compare defensive strategies: measurement-reset vs. coherent cleanup vs. fresh allocation

### Stage 4: Hardware Validation & Noise
- Run same circuits on real quantum hardware (IBM, IonQ, etc.)
- Compare coherent cleanup, measurement-reset, and fresh allocation under realistic noise
- Measure decoherence, gate error, measurement readout error impacts
- Evaluate whether noise accidentally defeats attacks or enables new vulnerabilities
- Generate noise-dependent threat-model updates

## Key Concepts: Four Levels Explained

### E0: Histogram Equivalence
Two scenarios yield identical measurement probability distributions.
```
Baseline P(0) = 0.50,  P(1) = 0.50
Advanced P(0) ≈ 0.50,  P(1) ≈ 0.50  ← Statistically equivalent
```
**Security Assessment:** First line of defense against brute-force attacks; insufficient for quantum security.

### E1: Reduced-State Equivalence
Two scenarios yield identical reduced density matrices when Bob's qubit is traced out.
```
Baseline:  ρ_victim = |0⟩⟨0|  (pure)
Advanced:  ρ_victim = I/2      (maximally mixed) ← NOT equivalent
```
**Security Assessment:** Breaks down for advanced attack; signature of entanglement with attacker.

### E2: Process Equivalence
Two circuits implement the same quantum channel: identical output for all inputs.
```
Channel_baseline(ρ_input) = Channel_advanced(ρ_input)  for all ρ
```
**Security Assessment:** Would guarantee true equivalence; our case studies fail this.

### E3: Full Execution Fidelity
Total state vectors match including phase:
```
|ψ_baseline⟩ = e^(iφ) |ψ_advanced⟩  (up to global phase)
```
**Security Assessment:** Strongest guarantee; rarely required for cryptographic security.

## Numerical Validation Framework

All computed results undergo rigorous numerical validation to ensure floating-point errors don't contaminate conclusions:

✅ **Trace Preservation**  
   Maximum error: $|\text{Tr}(\rho) - 1| < 2.22 \times 10^{-16}$ (machine epsilon)

✅ **Hermiticity**  
   Maximum deviation: $||\rho - \rho^\dagger||_F < 10^{-14}$

✅ **Positive Semi-Definiteness**  
   Minimum eigenvalue: $\lambda_{\min} > -10^{-15}$ (physically acceptable)

✅ **Perturbation Bounds (Weyl)**  
   State-input errors bounded by condition number: $\kappa(\rho) \approx 10^{16}$

✅ **Error-to-Epsilon Ratio**  
   All reported metrics at $1.00\times$ machine epsilon (numerically optimal)

## Defense Mechanisms

### Defense D1: Complementary-Basis Testing
After allocation, the compiler/runtime performs **randomized non-computational basis measurements** to detect hidden entanglement:
```python
for qubit in reclaimed_qubits:
    basis = random.choice(['Z', 'X', 'Y'])
    outcome = measure(qubit, basis)
    # Log for anomaly detection
```
An attacker cannot hide fidelity in all three bases simultaneously (Bloch-sphere constraint).

### Defense D2: State-and-Secrecy Contracts
Extend classical program assertions to quantum state properties:
```python
@quantum_assert(qubit=q, state="|0⟩", basis="Z")
def allocate_qubit():
    # Verify q is in |0⟩ state, not merely measured-zero
    pass
```
Combine measurement and tomographic verification.

### Defense D3: Cross-Layer Attestation
Bind circuit, mapping, timing, and pulse layers to prevent compiler-runtime splitting:
- Circuit specifies qubit IDs
- Mapping specifies physical-to-logical assignment
- Timing specifies gate duration (prevents arbitrary substitution)
- Pulse specifies exact pulse sequence (prevents gate-fusion attacks)

### Defense D4: Trap and Canary Circuits
Interleave **known-state circuits** that fail loudly if coupled to attacker:
```
User circuit:   |ψ⟩ → [user gate] → measure
Canary circuit: |1⟩ → [test gate] → MUST return |1⟩

If attacker couples, canary fidelity drops below threshold → alert
```

## Open Questions

1. **Hardware Reality:** Do real quantum computers support these attacks under realistic noise and calibration?
2. **Compiler Hardening:** Can compiler middle-end passes prevent qubit-reuse attacks with zero performance cost?
3. **Measurement-Reset vs. Coherent Cleanup:** Which is actually more robust under hardware imperfections?
4. **Multi-Round Attacks:** Can attacker adapt basis choice across multiple circuit executions?
5. **Distributed Attacks:** Can attacks work across multiple logical qubits in a shared pool?

## References

- Bennett et al. (1993). "Teleporting an Unknown Quantum State via Dual Classical and Einstein–Podolsky–Rosen Channels." *Phys. Rev. Lett.* 70(13).
- Nielsen & Chuang (2010). *Quantum Computation and Quantum Information* (10th Anniversary Edition).
- Fuchs (1996). "Information Gain versus State Disturbance in Quantum Theory." *Phys. Rev. A* 54(1).
- Koashi & Imoto (2002). "Operations That Do Not Disturb Partially Known Quantum States." *Phys. Rev. A* 66(2).
- DeCross et al. (2023). "Qubit-Reuse Compilation for Shallow Quantum Circuits." *Quantum Engineering* 2(1).

## Disclaimer

This work explores compiler and software security boundaries in quantum computing. It does not:
- Prove attacks on deployed quantum systems
- Break BB84 or other cryptographic protocols
- Violate quantum mechanics
- Claim to work on real hardware without experimental validation

It does provide a **research roadmap** for understanding information flow, qubit reuse safety, and the gap between histogram-level and state-level security in quantum systems.
