# Research Agenda: Four-Stage Plan for Publication

## Executive Summary

This document outlines a four-stage research program to advance the findings on quantum qubit reuse security from research draft to publication-ready work. Each stage builds on validated results from the previous stage.

## Stage 1: Semantic Wire Mapping & Fixed-Input Tests

### Objectives
1. Establish ground truth through Quirk circuit exports
2. Verify circuit correctness across all input configurations
3. Compute exact density matrices for all 12 branches
4. Generate numerical validation baseline

### Detailed Plan

#### 1.1 Quirk Export Validation
- **Current State:** Supplied Quirk exports (baseline, intercept-resend, advanced)
- **Task:** Extract and validate all 32 complex amplitudes per circuit
- **Verification:** Reconstruct density matrices and verify against symbolic computation
- **Deliverable:** `data/quirk_exports/amplitudes_verified.json`

#### 1.2 Semantic Wire Assignment
```
Wire 0: Alice's basis choice (b ∈ {0,1})
Wire 1: Alice's value (v ∈ {0,1})  
Wire 2: Eve's basis choice (e ∈ {0,1}) [only for advanced]
Wire 3: Bob's basis choice (c ∈ {0,1})
Wire 4: Eve's measurement outcome (hidden in victim system)
```

**Task:** Map each wire through SWAP permutations and verify semantic consistency across circuits.

**Deliverable:** `data/semantic_mapping.json` documenting wire roles

#### 1.3 Fixed-Input Analysis
For each $(v, b) \in \{0,1\}^2$:
- Prepare Alice's state with fixed value and basis
- Enumerate all Eve measurement outcomes (2 outcomes for 1 qubit)
- Compute Bob's probabilities for both basis choices (c ∈ {0,1})
- Verify histogram conservation

**Example workflow:**
```
for v in [0, 1]:
    for b in [0, 1]:
        alice_state = prepare_alice(value=v, basis=b)
        for eve_outcome in [0, 1]:
            victim_state = trace_eve(alice_state, eve_outcome)
            for c in [0, 1]:
                bob_prob = measure_bob(victim_state, basis=c)
                store(v, b, eve_outcome, c, bob_prob)
```

**Output:** 8 × 2 = 16 data points per scenario (baseline, intercept-resend, advanced)

#### 1.4 Numerical Validation Baseline
Apply rigorous validation to all computed states:
- ✅ Trace preservation: $|\text{Tr}(\rho) - 1| < 10^{-10}$
- ✅ Hermiticity: $||\rho - \rho^\dagger||_F < 10^{-14}$
- ✅ Positive semi-definiteness: $\lambda_{\min} > -10^{-14}$
- ✅ Purity constraints: $0 \leq \text{Tr}(\rho^2) \leq 1$

**Deliverable:** Numerical validation report with per-state metrics

### Stage 1 Success Criteria
- ✅ All Quirk exports validated with error < 10^{-15}
- ✅ 12 branches computed and verified
- ✅ No numerical validation failures
- ✅ Histogram conservation demonstrated analytically and numerically
- ✅ Ground-truth database ready for Stage 2 analysis

### Timeline Estimate
**2-3 weeks** (includes code development, validation troubleshooting, documentation)

---

## Stage 2: Attacker-Information Metrics

### Objectives
1. Quantify Eve's accessible information about Alice's state
2. Measure basis/value distinguishability across all scenarios
3. Compute mutual information and Holevo capacity
4. Identify which information flows through hidden subsystem

### Detailed Plan

#### 2.1 Holevo Information: $\chi(X : E)$

**Definition:** Attacker's maximum accessible information about Alice's prepared state.

$$\chi(X : E) = \max_{\text{measurements}} I(X : M)$$

where $X$ is Alice's state type (basis + value), and $M$ is attacker's measurement outcome.

**Computation:**
```python
# Eve has reduced density matrix ρ_E (after tracing Bob)
# Prepare ensemble: {p_x, ρ_x} where x ∈ {00, 01, 10, 11}

# Holevo information
chi = S(average_rho) - sum(p_x * S(rho_x))
# where S(ρ) = -Tr(ρ log₂ ρ) is von Neumann entropy
```

**Deliverable:** Holevo information table for all scenarios

#### 2.2 Mutual Information: $I(V : E)$ and $I(B : E)$

**Value Distinguishability:**
$$I(V : E) = H(V) - H(V|E)$$
where $V \in \{0,1\}$ is Alice's value, and $E$ is Eve's measurement outcome.

**Basis Distinguishability:**
$$I(B : E) = H(B) - H(B|E)$$
where $B \in \{0,1\}$ is Alice's basis choice.

**Computation:**
```python
# For each scenario:
for v in [0, 1]:
    for b in [0, 1]:
        victim = get_victim_state(v, b)
        eve_dm = trace_bob(victim)
        
        # Eve measures in optimal basis
        probs = get_marginals(eve_dm)
        
        # Compute mutual information
        I_V_E = mutual_info(V_distribution, probs)
        I_B_E = mutual_info(B_distribution, probs)
```

**Deliverable:** Information-flow matrix showing which attacks leak basis vs. value

#### 2.3 Phase-Sensitive Observables

**Motivation:** Eve can measure only computational outcomes. But phase-sensitive observables (Pauli X, Y) on unmeasured qubits reveal superposition structure.

**Computation:**
```python
# For each scenario:
victim = get_victim_state(alice_value, alice_basis)

# Bloch vector: ⟨σ_x⟩, ⟨σ_y⟩, ⟨σ_z⟩
bloch_x = Tr(victim @ pauli_x)
bloch_y = Tr(victim @ pauli_y)
bloch_z = Tr(victim @ pauli_z)

# Purity (identifies mixed states)
purity = Tr(victim @ victim)

# Store results
record_observables(scenario, alice_value, alice_basis, 
                  bloch_x, bloch_y, bloch_z, purity)
```

**Interpretation:**
- Baseline: Bloch vector has magnitude 1 (pure state)
- Attack: Bloch vector has magnitude < 1 (mixed state) → traces entanglement

**Deliverable:** Bloch-vector table and purity comparison

#### 2.4 Comparative Analysis

| Metric | Baseline | Intercept-Resend | Advanced | Interpretation |
|--------|----------|------------------|----------|-----------------|
| $\chi(X:E)$ | 0 | ? | ? | Attacker accessible info |
| $I(V:E)$ | 0 | ? | ? | Value leakage |
| $I(B:E)$ | 0 | ? | ? | Basis leakage |
| Purity | 1 | 1/2 | 1/2 | Entanglement signature |
| Bloch magnitude | 1 | ? | ? | Coherence marker |
| Fidelity with baseline | 1 | 0.25 | 0.4268 | State similarity |

**Analysis Questions:**
1. Does advanced attack achieve nonzero $I(V:E)$ or $I(B:E)$?
2. Does any information flow through hidden subsystem without measurement?
3. Can Eve distinguish Alice's basis and value purely through sideband coupling?

### Stage 2 Success Criteria
- ✅ Holevo information computed for all scenarios
- ✅ Mutual information matrices generated
- ✅ Phase-sensitive observables tabulated
- ✅ Hidden-subsystem information pathways identified
- ✅ Comparative analysis table complete
- ✅ Statistical significance tests (null hypothesis testing) passed

### Timeline Estimate
**3-4 weeks** (includes information-theoretic calculations, verification, manuscript draft)

---

## Stage 3: Malicious Compiler Prototype

### Objectives
1. Build controlled research prototype implementing attacks
2. Measure fidelity of copied information
3. Evaluate detection difficulty
4. Test defensive strategies

### Detailed Plan

#### 3.1 Toy-Model CNOT Insertion

**Prototype Architecture:**
```
User Circuit (Protected):
    q[0:3] = user_quantum_circuit()
    
Compiler Transformation (Adversarial):
    add_cnot(control=q_attacker, target=q_user[selected])
    
Measurement & Extraction:
    attacker_outcome = measure(q_attacker, basis="adaptive")
    route_result_to_unauthorized_output()
```

**Task:** Implement in Python with NumPy backend.

**Constraints:**
- No modification to user-visible circuit
- Gates appear after circuit inspection points
- Information extraction invisible at histogram level

**Deliverable:** Working prototype code in `src/quantum_reuse/attacks/cnot_insertion.py`

#### 3.2 Detection Difficulty Measurement

**Experiment:** Run attack and measure metrics that would detect it:

```python
def measure_detectability(scenario="advanced", num_trials=100):
    detections = {
        "histogram_divergence": [],
        "purity_change": [],
        "fidelity_loss": [],
        "trace_distance": [],
        "bloch_deviation": []
    }
    
    for trial in range(num_trials):
        baseline_state = get_baseline(scenario)
        attack_state = get_attack(scenario)
        
        detections["histogram_divergence"].append(
            total_variation_distance(
                measure(baseline_state, "Z"),
                measure(attack_state, "Z")
            )
        )
        
        detections["purity_change"].append(
            abs(purity(baseline_state) - purity(attack_state))
        )
        
        detections["fidelity_loss"].append(
            1 - fidelity(baseline_state, attack_state)
        )
        
        detections["trace_distance"].append(
            trace_distance(baseline_state, attack_state)
        )
        
        detections["bloch_deviation"].append(
            norm(bloch_vector(baseline_state) - 
                 bloch_vector(attack_state))
        )
    
    return detections
```

**Metrics:**
- **Histogram divergence:** Would statistical tests detect the attack?
- **Purity change:** Would state tomography reveal the attack?
- **Fidelity loss:** How far is the attacked state from baseline?
- **Trace distance:** How orthogonal are the attacked and baseline spaces?
- **Bloch deviation:** How much does the Bloch vector rotate?

**Threshold Definition:**
```
Detectable if: any(metric > threshold for threshold in detection_thresholds)
Stealthy if:   all(metric < threshold for threshold in detection_thresholds)
```

**Deliverable:** Detection-difficulty report with ROC curves

#### 3.3 Defensive Strategy Evaluation

**Test three defense mechanisms:**

1. **Fresh allocation** (baseline)
   - Qubit deallocated and lost
   - Cost: ~zero (default)
   - Attack success: None (no workspace)

2. **Measurement-reset**
   - Qubit measured in Z basis, reset to |0⟩
   - Cost: One measurement + reset gate
   - Attack success: Residual phase? Leakage state?

3. **Coherent cleanup**
   - Teleportation-based cleanup (from Stage 1)
   - Cost: Five-qubit circuit overhead
   - Attack success: Can teleportation be coupled?

**Experiment:**
```python
def compare_defenses(user_circuit, secret_value):
    results = {}
    
    for defense in ["none", "measurement_reset", "coherent_cleanup"]:
        protected_circuit = apply_defense(user_circuit, defense)
        
        # Run attack
        attacker_outcome = simulate_malicious_compiler(protected_circuit)
        
        # Measure success
        results[defense] = {
            "fidelity_of_stolen_info": fidelity(attacker_outcome, secret_value),
            "victim_histogram_distortion": histogram_distance(...),
            "overhead_gates": count_gates(defense),
            "overhead_time": measure_latency(defense)
        }
    
    return results
```

**Deliverable:** Comparative defense-effectiveness table

#### 3.4 Adaptive Attack Strategies

**Multi-round adaptation:** Can attacker improve fidelity by adapting basis per round?

```python
def adaptive_multi_round_attack(user_circuit_generator, num_rounds=10):
    attacker_history = {"outcomes": [], "optimal_bases": []}
    
    for round in range(num_rounds):
        # User runs circuit, attacker doesn't know future basis
        user_circuit = user_circuit_generator(round)
        
        # Attacker chooses basis (adaptive)
        if round == 0:
            basis = "Z"  # Default
        else:
            basis = choose_adaptive_basis(
                attacker_history["outcomes"],
                user_circuit_params
            )
        
        # Run attack
        victim_state = run_user_circuit(user_circuit)
        attacker_measurement = measure(victim_state, basis=basis)
        
        attacker_history["outcomes"].append(attacker_measurement)
        
        # Update strategy based on outcome
        attacker_history["optimal_bases"].append(basis)
    
    # Evaluate cumulative information gain
    mutual_info = compute_mutual_information(
        attacker_history["outcomes"],
        user_circuit_params
    )
    
    return mutual_info
```

**Deliverable:** Adaptive-attack performance curves (information gain vs. rounds)

### Stage 3 Success Criteria
- ✅ Malicious compiler prototype implemented
- ✅ Attack succeeds (fidelity > baseline by measurable amount)
- ✅ Attack is stealthy (passes defensive statistical tests in controlled setting)
- ✅ Defense mechanisms ranked by cost-benefit
- ✅ Adaptive strategies quantified
- ✅ Prototype code open-sourced for research community

### Timeline Estimate
**4-6 weeks** (includes prototype development, testing, edge-case handling, paper drafting)

---

## Stage 4: Hardware Validation & Noise Analysis

### Objectives
1. Run circuits on real quantum hardware
2. Evaluate coherence-time constraints
3. Measure noise impact on attacks
4. Generate hardware-specific threat-model updates

### Detailed Plan

#### 4.1 Hardware Platform Selection

**Candidates:**
- IBM Quantum (public access, U.S.)
- IonQ (trapped-ion, high fidelity)
- Rigetti (hybrid classical-quantum)
- Neutral atoms (emerging, good coherence)

**Selection criteria:**
- Access: Public or research partnership
- Fidelity: $T_2 > 10$ μs (gates in 10-100 ns range)
- Circuit depth: Can run 5+ qubit circuits
- Allocation: Can test qubit reuse in memory model

**Deliverable:** Test-run plan for each platform

#### 4.2 Coherent Teleportation Cleanup on Hardware

**Experiment:**
```python
def test_coherent_cleanup_on_hardware(backend):
    """
    Test Claim 1: Coherent teleportation cleanup on real hardware.
    """
    random_states = generate_random_single_qubit_states(N=100)
    fidelities = []
    
    for psi in random_states:
        # Build circuit
        circuit = QuantumCircuit(5)
        circuit.initialize(psi, 0)  # Source qubit
        circuit.barrier()
        
        # Apply coherent cleanup
        circuit = add_coherent_cleanup(circuit, source=0, dest=4)
        circuit.barrier()
        
        # Verify source and ancillas are |0⟩
        circuit.measure_all()
        
        # Run on backend
        result = execute(circuit, backend)
        
        # Compute fidelity
        final_state = get_final_state(result)
        expected_state = basis_state_1hot(4)  # |00001⟩
        
        fidelity = compute_fidelity(final_state, expected_state)
        fidelities.append(fidelity)
    
    return {
        "mean_fidelity": np.mean(fidelities),
        "min_fidelity": np.min(fidelities),
        "std_fidelity": np.std(fidelities),
        "platform": backend.name
    }
```

**Deliverable:** Fidelity report across platforms

#### 4.3 Attack Success Under Noise

**Experiment:** Insert malicious CNOT on hardware and measure attack effectiveness:

```python
def test_attack_on_hardware(backend, attack_depth=1):
    """
    Test attack effectiveness on real hardware.
    """
    scenarios = ["baseline", "intercept_resend", "advanced"]
    results = {}
    
    for scenario in scenarios:
        user_circuit = get_bb84_circuit(scenario)
        
        # Insert malicious CNOT
        attacker_circuit = insert_malicious_cnot(
            user_circuit, 
            control_qubit=3, 
            target_qubit=4,
            depth=attack_depth
        )
        
        # Run on hardware
        job = execute(attacker_circuit, backend, shots=1024)
        result = job.result()
        
        # Measure attack success
        histogram = result.get_counts()
        
        # Compare with baseline
        fidelity_with_baseline = compute_histogram_fidelity(
            histogram, 
            baseline_histogram
        )
        
        results[scenario] = {
            "fidelity": fidelity_with_baseline,
            "histogram": histogram,
            "noise_floor": estimate_noise(histogram)
        }
    
    return results
```

**Deliverable:** Hardware-specific attack-success rates

#### 4.4 Decoherence-Time Constraints

**Experiment:** Measure how attack fidelity degrades with gate duration:

```python
def measure_decoherence_constraint(backend):
    """
    How long can attacker maintain entanglement?
    """
    gate_delays = np.linspace(10, 1000, 50)  # ns
    fidelities = []
    
    for delay in gate_delays:
        circuit = prepare_entangled_state()
        circuit.delay(delay, qubit_a)
        circuit.delay(delay, qubit_u)
        circuit.barrier()
        
        # Measure entanglement fidelity
        result = execute(circuit, backend)
        fidelity = measure_entanglement_fidelity(result)
        fidelities.append(fidelity)
    
    # Fit decay curve
    T2_estimate = fit_exponential_decay(gate_delays, fidelities)
    
    return {
        "T2_measured": T2_estimate,
        "fidelities": fidelities,
        "gate_delays": gate_delays
    }
```

**Deliverable:** $T_2$ coherence-time estimates and attack-viability windows

#### 4.5 Noise-Dependent Threat-Model Updates

**Analysis:**
- Does noise accidentally defeat attacks?
- Do attacks become stronger under certain noise types?
- What's the minimum hardware fidelity needed to mount attacks?

**Deliverable:** Updated threat model with hardware constraints

### Stage 4 Success Criteria
- ✅ Circuits run successfully on ≥ 2 hardware platforms
- ✅ Coherent cleanup fidelity measured (compare theory vs. experiment)
- ✅ Attack success rates quantified under realistic noise
- ✅ Decoherence time measured for attacker-victim entanglement
- ✅ Hardware-specific defense recommendations generated
- ✅ Manuscript ready for submission

### Timeline Estimate
**6-8 weeks** (includes hardware access negotiation, queue wait times, result analysis)

---

## Overall Research Timeline

| Stage | Duration | Cumulative |
|-------|----------|-----------|
| Stage 1: Semantic Mapping | 2-3 weeks | 2-3 weeks |
| Stage 2: Information Metrics | 3-4 weeks | 5-7 weeks |
| Stage 3: Compiler Prototype | 4-6 weeks | 9-13 weeks |
| Stage 4: Hardware Validation | 6-8 weeks | 15-21 weeks |
| **Buffer + Revisions** | 2-4 weeks | **17-25 weeks** |

**Estimated Total:** 4-6 months to publication-ready manuscript

---

## Funding & Collaboration Opportunities

### Grant Targets
- NSF Quantum Computing Program
- DoE Office of Science (Quantum Systems Accelerator)
- IARPA QEO (Quantum Enhanced Optimization)
- Semiconductor Research Corporation (SRC)

### Academic Collaborations
- University quantum-computing labs (IBM Q network)
- Quantum-compiler research groups
- Computer security groups (side-channel attacks)

### Industry Partnerships
- IBM Quantum (hardware access)
- IonQ (trapped-ion platform)
- Amazon Braket (multi-platform access)
- Qiskit Foundation (compiler integration)

---

## Publication Strategy

### Primary Venues
1. **Quantum Information Processing** (journal, theory-focused)
2. **IEEE TQE** (IEEE Transactions on Quantum Engineering, hardware)
3. **CCS** (ACM Conference on Computer and Communications Security, threat model)
4. **QIP 2027** (Quantum Information Processing, preprint)

### Manuscript Structure
- **Paper 1 (Theory):** Coherent cleanup theorem + information-theoretic bounds
- **Paper 2 (Case Study):** Educational spy-detector analysis with numerical validation
- **Paper 3 (Hardware):** Real-device measurements and noise impact
- **Paper 4 (Defense):** Defensive strategies and cross-layer attestation

---

## Risk Mitigation

### Technical Risks
| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Coherent cleanup has subtle flaw | Low | Symbolic verification in SymPy; peer review |
| Attacks don't work on real hardware | Medium | Test on simulators first; iterate design |
| Noise destroys useful information | Medium | Stage 1-2 can proceed; Stage 3 adapts |
| Hardware access delayed | Medium | Use public IBM Q; negotiate backup access |

### Research Risks
| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Results not novel (known in literature) | Low | Lit search during Stage 1; early preprint |
| Ethical concerns about attack publicization | Low | Responsible disclosure to NIST/NSF |
| Funding limitations | Medium | Start with university resources; apply for grants mid-stream |

---

## Success Metrics (Acceptance Criteria)

✅ **Stage 1 complete:** Numerical validation report shows zero failures
✅ **Stage 2 complete:** Information-theoretic analysis published
✅ **Stage 3 complete:** Prototype attack works with fidelity > 40%
✅ **Stage 4 complete:** Hardware results within 2× of simulator predictions
✅ **Defense analysis:** At least 3 viable defense mechanisms ranked
✅ **Open source:** Code, data, and notebooks on GitHub
✅ **Citation ready:** Paper accepted or in review

---

## References & Reading List

- **Coherent cleanup:** Bennett et al. "Teleporting an Unknown Quantum State" (1993)
- **Information disturbance:** Fuchs (1996), Koashi & Imoto (2002)
- **Quantum compiler threats:** DeCross et al. (2023), Ben-David et al. (2020)
- **Hardware security:** Cross et al. "Openqasm 3: A Broader and Deeper Quantum Assembly Language" (2022)
