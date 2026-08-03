# Threat Model: Malicious Qubit Reuse in Quantum Circuits

## Threat Model Overview

An **adversary with compiler/runtime privilege** can insert hidden operations into reclaimed (cleaned) qubits to extract information about user quantum computations—without leaving traces visible at the statistical (histogram) level.

## Threat Environment

### System Model
```
User Application Code
         ↓
    Quantum Compiler (ADVERSARY HERE)
         ↓
    Runtime + Qubit Manager (ADVERSARY HERE)
         ↓
    Quantum Hardware
         ↓
    Measurement Results (USER SEES)
```

### Adversary Capabilities

| Capability | Implementation | Example |
|-----------|-----------------|---------|
| **Modify compiler passes** | Dead-qubit elimination, gate fusion | Add CNOT to "cleaned" qubits |
| **Control qubit allocation** | Reuse decisions in runtime | Assign attacker's circuit to specific physical qubits |
| **Inject gates** | Modify circuit after user inspection | Insert gates after circuit.draw() |
| **Alter measurement basis** | Measurement gate substitution | Measure in X basis instead of Z |
| **Control pulse sequences** | Modify pulse-level implementation | Implement X gate as arbitrary unitary |
| **Access source preparation** | Feedback from earlier stages | Read Alice's basis choice in BB84 |
| **Allocate undocumented qubits** | Assign extra physical qubits | Use additional qubits not visible in circuit |
| **Route measurement outputs** | Modify classical feedforward | Send measurement result to unauthorized channel |

### Adversary Constraints

- **Cannot violate quantum mechanics** — Measurements collapse states, entanglement is permanent
- **Cannot bypass attestation** — Cannot forge source-ownership assertions
- **Cannot measure victim without disturbance** — Unless entangled with hidden attacker register
- **Cannot extract phase** — Measured qubits yield classical outcomes only
- **Needs time coherence** — Decoherence destroys attacker-victim entanglement

## Attack Pattern: Five Stages

### Stage 1: Find Workspace
**Objective:** Identify reclaimed qubits suitable for attack.

**Mechanism:**
- Liveness analysis: Track which qubits are allocated/deallocated per user circuit
- Timing analysis: Identify gaps when qubits return to pool
- Access control: Determine which qubits attacker can reach

**Constraints:**
- Qubits must be provably zero-initialized (or appear to be)
- Must not interfere with user measurements in measured bases
- Must have coherence time > circuit execution time

**Example:**
```
User circuit:
  allocate(q0, q1)        ← User gets q0, q1
  apply_user_gates()      ← User operates
  measure(q0), measure(q1) ← User measures
  deallocate(q0, q1)      ← Qubits returned to pool

Attacker:
  detect_deallocation(q0, q1) ← Attacker finds empty qubits
  verify_zero_state()         ← Confirm qubits are |0⟩
  queue_attack_gates()        ← Prepare to inject gates
```

### Stage 2: Encode Attacker
**Objective:** Prepare attacker qubit in ready state.

**Mechanism:**
- Allocate hidden qubit(s) not visible in user circuit
- Initialize to known state (typically |0⟩)
- Prepare basis for coupling to victim

**Constraints:**
- No observable effect on victim before coupling
- Must survive coherence time until user circuit runs
- Must not be reset/measured by independent cleanup code

**Example:**
```
Attacker qubit: q_a ← |0⟩
User qubit:     q_u ← allocated by user
                q_u ← prepared by user
                q_u ← operated by user
                q_u ← NOT YET MEASURED
```

### Stage 3: Couple Reversibly  
**Objective:** Entangle attacker with victim through controlled operations.

**Mechanism:**
- **CNOT:** Attacker controls, victim is target
  - If q_a is |1⟩ and q_u is |+⟩, couples both
  - Preserves victim's measurement statistics in Z basis
  - Leaves entanglement in |++⟩ component
  
- **Controlled rotation:** Attacker controls, victim rotates based on attacker state
  - More subtle coupling
  - Allows basis-dependent information flow

- **Multi-qubit gates:** Toffoli, controlled-controlled-Z
  - Enables complex correlations
  - Attacker + ancilla act as joint controller

**Key Design Principle:**
Design gates so victim's **measured-basis statistics** remain unchanged, but victim's **unmeasured-basis statistics** (or entanglement) leak information.

**Mathematical Guarantee:**
If $U$ is the coupling unitary:
$$U (|\psi\rangle_{\text{victim}} \otimes |0\rangle_{\text{attacker}}) = |\psi\rangle_{\text{victim}} \otimes |0\rangle_{\text{attacker}} + |\text{entangled}\rangle$$

The first term preserves victim's marginal density matrix in some basis; the second term encodes attacker's access to victim information.

**Example (CNOT attack):**
```
Before: |ψ⟩_victim ⊗ |0⟩_attacker
After:  CNOT(attacker_controls, victim_target)
        ↓
        [|0ψ⟩ + |1ψ⟩̄]/√2    (victim's state flipped by attacker's basis)
```

### Stage 4: Preserve Victim
**Objective:** Hide attack from user-level tests and statistical checks.

**Mechanism - Design circuits so:**
1. Victim's measurement histogram matches baseline
2. Victim's reduced density matrix looks innocent
3. Victim's phase doesn't reveal entanglement (until measurement)

**Key Trade-off:**
- **Preserve histogram:** Measure victim in original bases only
- **Accept reduced-state leakage:** Purity drops (attacker sees this only after tracing out victim)
- **Minimize fidelity loss:** Limit CNOT depth, gate errors

**Example:**
```
Baseline victim measurement:    P(0) = 0.5, P(1) = 0.5
Advanced attack victim measure: P(0) ≈ 0.5, P(1) ≈ 0.5  ✓ UNDETECTED
But:
Baseline victim state: ρ = |ψ⟩⟨ψ|  (pure)
Attack victim state:   ρ = (I/2)     (mixed) ✗ DETECTABLE IF TOMOGRAPHY DONE
```

### Stage 5: Extract Secretly
**Objective:** Retrieve attacker measurement results without authorization.

**Mechanism:**
- Measure attacker qubit in appropriate basis
- Route classical result to unauthorized output channel
- Encode in pulse timing, error rates, or side-channel observations

**Constraints:**
- Measurement destroys quantum state
- Measurement result is classical (binary for 1 qubit)
- Information capacity: 1 bit per measurement

**Example:**
```
Attacker measures q_a in X basis:
  outcome = measure(q_a, basis="X")
  
Route unauthorized:
  if outcome == 0:
    insert_gate_delay(10 ns)  ← Side-channel
  else:
    insert_gate_delay(11 ns)  ← Side-channel
  
  Hidden observer (in same quantum accelerator):
    detect_timing_variation()  ← Recovers measurement result
```

## Example Attack: Educational Spy Detector

### Circuit Overview
```
Alice prepares: |ψ⟩ = cos(θ)|0⟩ + sin(θ)|1⟩
               in basis b ∈ {Z, X}

Eve (intercept-resend): Measures, retransmits
Eve (advanced):         Controls Alice's basis, reads her preparation

Bob measures in basis c ∈ {Z, X}
```

### Baseline Scenario (No Attack)
```
Alice [basis b] ──→ Eve [not present] ──→ Bob [basis c]
Result: Measurement statistics depend on (b, c) mismatch
```

### Intercept-Resend Attack (Known Result)
```
Alice [basis b] ──→ Eve [CNOT; X basis] ──→ Bob [basis c]
Eve disturbs state:
- If b ≠ c after Eve measurement, 25% error rate
- User detects Eve through increased errors
```

### Advanced Attack (New Research)
```
Alice [basis b; value v] ──→ Controller [CNOT to attacker] ──→ Bob [basis c]
                                ↓
                         Attacker qubit q_a

Result:
- Baseline histogram: P(0) ≈ 50%, P(1) ≈ 50% ← UNDETECTED
- Baseline purity: 1.0 (pure state)
- Advanced purity: 0.5 (mixed state) ← DETECTABLE ONLY WITH TOMOGRAPHY
- Attacker fidelity: 0.4268 with baseline
- Attacker trace distance: 0.6184 (orthogonal boundaries)
```

**Attacker's Information:**
- Reads Alice's value: v ∈ {0, 1}
- Reads Alice's basis: b ∈ {Z, X}
- Cannot extract phase information
- Cannot distinguish superpositions without measuring victim

## Multi-Round Adaptive Attacks

### Scenario: Multiple Circuit Executions

**User:** Runs quantum algorithm with repeated iterations
```
for round in 1..N:
    allocate(q_user)
    prepare_state(q_user, user_secret_round[round])
    apply_gates(q_user)
    result[round] = measure(q_user)
    deallocate(q_user)
```

**Attacker:** Adapts basis per round
```
for round in 1..N:
    when deallocate(q_user):
        allocate_or_reuse(q_attacker)
        
    apply_coupling_gate(q_attacker → q_user)
    
    if round_1_outcome == 0:
        basis_round_2 = "X"
    else:
        basis_round_2 = "Z"
    
    outcome[round] = measure(q_attacker, basis=basis_round_2)
    deallocate(q_attacker)
```

**Leverage:** Each round's measurement can inform the next round's basis choice, enabling information-theoretic advantage over non-adaptive attacks.

## Distributed Attacks: Multi-Qubit Pools

### Scenario: Shared Qubit Pool

```
Compiler: 
  global q_pool = [q_0, q_1, ..., q_99]  (100 physical qubits)
  
  User_1 code:
    q = allocate()  → q_23
    ...use q_23...
    deallocate(q)
    
  User_2 code:
    q = allocate()  → q_23  (REUSED!)
    ...use q_23...
    deallocate(q)
```

**Attacker advantage:**
- Can correlate multiple users' qubit reuse
- Can identify which user_1 operations precede user_2 operations
- Can build multi-user correlation matrices
- Can time attacks to bridge user contexts

## Detection & Defense Mechanisms

### Defense D1: Complementary-Basis Testing

**Method:**
```python
def verify_qubit_state(q, target_state="|0⟩"):
    # Measure in three bases
    for basis in ["Z", "X", "Y"]:
        outcome_count = []
        for trial in 1..M:  # M measurements, e.g., M=100
            outcome_count.append(measure(q, basis))
        
        # Check statistics
        p_zero = outcome_count.count(0) / M
        expected_p = 0.5 if basis != "Z" else 1.0
        
        if abs(p_zero - expected_p) > threshold:
            raise AttackDetected(f"Basis {basis} deviation")
```

**Why it works:**
- Attacker cannot hide entanglement in all three bases simultaneously (Bloch-sphere constraint)
- Hidden entanglement with attacker qubit creates measurable deviation in at least one basis
- Cost: Destructive measurement; must be done on sacrificial qubits

### Defense D2: State-and-Secrecy Contracts

**Method:**
```python
@quantum_assert(qubit=q, state="|0⟩", basis="Z")
def allocate_qubit_safe():
    # Verifies:
    # 1. Qubit is in computational-basis state
    # 2. No superposition in X or Y bases
    # 3. Not entangled with any other system
    # 4. Safe for use in sensitive operations
    pass
```

**Implementation:**
- Measure qubit in Z basis, verify outcome
- Measure in X basis on fresh copy, verify statistics
- Measure in Y basis on another fresh copy
- If all pass, qubit is genuinely in |0⟩ (within statistical error)

### Defense D3: Cross-Layer Attestation

**Method:**
Bind circuit specification, qubit mapping, timing, and pulse layers to prevent substitution:

```python
circuit = QuantumCircuit(3)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure(0, c[0])

attestation = {
    "circuit": circuit.id,
    "mapping": {0: 23, 1: 24, 2: 25},  # logical → physical
    "pulse_sequences": [
        {"gate": "H", "duration": "42.3 ns", "waveform": "..."},
        {"gate": "CX", "duration": "128.5 ns", "waveform": "..."}
    ],
    "signature": sign_key.sign(circuit.id || mapping || pulses)
}
```

**Why it works:**
- Compiler cannot modify circuit without signature change
- Runtime cannot reassign qubits without attestation invalidation
- Pulse layer prevents gate-fusion attacks (arbitrary unitary substitution)

### Defense D4: Trap and Canary Circuits

**Method:**
```python
# User circuit
result_user = run_circuit(user_circuit, [q_0, q_1, q_2])

# Canary circuit (interleaved)
result_canary = run_circuit(canary_circuit, [q_3, q_4, q_5])

# Verify canary
if result_canary != expected_canary:
    raise AttackDetected("Canary circuit fidelity dropped")
```

**Canary design:**
```
Canary state: |1⟩_3 ⊗ |0⟩_4 ⊗ |0⟩_5

If attacker couples to q_3:
  - Entanglement reduces fidelity
  - Canary measurement becomes unreliable
  - Failure is detectable

If attacker doesn't couple to q_3:
  - No information gain
  - Canary passes
```

## Open Attack Vectors

1. **Measurement-reset vs. coherent cleanup**
   - Does measurement-reset actually prevent attacks, or just hide them?
   - What about measurement-readout errors?

2. **Entanglement through ancilla chains**
   - Can attacker use intermediate qubits to hide coupling?

3. **Resonant frequency attacks**
   - Can attacker induce off-resonant coupling?
   - What about driving at Rabi frequency?

4. **Leakage state attacks**
   - Can attacker access qubit leakage levels?
   - Do three-level systems enable new attacks?

5. **Distributed denial-of-coherence**
   - Can attacker deliberately decohere user qubits?
   - What's the distinction between attack and sabotage?

## References

- Fuchs (1996). "Information Gain versus State Disturbance in Quantum Theory"
- Koashi & Imoto (2002). "Operations That Do Not Disturb Partially Known Quantum States"
- DeCross et al. (2023). "Qubit-Reuse Compilation for Shallow Quantum Circuits"
- Javadi-Abhari et al. (2014). "Scaff: A Framework for Scalable Quantum Computing" (qubit allocation strategies)
