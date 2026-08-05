# Threat Model

## 1. Source-Control Privilege Framework

This repository analyzes a **source-access threat model**: an adversary with
compiler or runtime control who can inject operations into reclaimed workspace
qubits. Informal terms such as "leaks information" or "gains access" obscure
whether the adversary actually distinguishes, preserves, or transmits the
protected value. This section defines four formally distinct privileges and
establishes the claim vocabulary used throughout the repository.

### 1.1 Privilege Definitions

| Privilege | Definition |
|-----------|------------|
| **Use** | A component may consume a protected value as an operand in an authorized operation. The operation may be coherent (no classical record produced). |
| **Read** | A component may learn or distinguish the protected value — i.e., the component, or a subsystem it controls, can determine the classical value at better than chance. |
| **Retain** | A component may preserve information about the protected value after the authorized operation ends — either in a quantum register that remains in a distinguishable state, or in a classical record. |
| **Export** | A component may transmit retained information across the computation boundary to an observer outside the authorized protocol. |

### 1.2 Non-Implications

The following implications are **false**. Each represents a common conflation
in informal security arguments.

```
use    ⊄  read      performing a coherent operation does not require learning the value
read   ⊄  retain    learning a value at one time does not require preserving it afterward
retain ⊄  export    preserving information within the computation boundary
                    does not constitute transmitting it outside that boundary
physical access ⊄  authorization
                    the ability to apply an operation does not constitute
                    permission to learn, keep, or transmit its classical content
```

### 1.3 Counterexamples

**CE-1: use does not imply read**

A CNOT gate _uses_ the control qubit to conditionally flip the target. The
operation is fully coherent: the control qubit is not measured, no classical
record of its value is produced, and the control qubit may remain in
superposition after the gate. The gate constructor gains zero classical
information about the control qubit value. This is the mechanism by which Eve
can couple an operation to a workspace qubit — and therefore _use_ the qubit —
without necessarily _reading_ Alice's value. Whether read occurs depends on
whether the operation maps the protected value to a classically distinguishable
record, not merely on whether an operation was performed on the qubit.

**CE-2: retain does not imply export**

When the Eve measurement basis matches Alice's basis ($e = b$), the fifth wire
$q_4$ retains $\rho_5 = |v\rangle\langle v|$ — a pure state that permits perfect
single-shot discrimination of Alice's bit. The fifth wire nonetheless remains a
qubit inside the five-wire computation. It is never transmitted to any party
outside the protocol boundary; the reduced state exists only as part of the
joint post-routing quantum state. Retention of perfectly discriminating
information within a computation does not constitute export, even when the
retained state is maximally informative. Export requires a transmission event
across the computation boundary to an observer outside the authorized protocol.

---

## 2. Security Claim Schema

Every security claim in this repository is expressible in the following form.

| Field | Content |
|-------|---------|
| **Actor** | The component or agent making the claim |
| **Resource** | The protected value or secret |
| **Allowed privilege** | Which of {use, read, retain, export} the actor is authorized for |
| **Forbidden privilege** | Which of {use, read, retain, export} the claim constrains |
| **Observation channel** | The quantum or classical channel through which the forbidden privilege could be exercised |
| **Lifetime** | Temporal scope of the constraint |
| **Evidence or enforcement** | The test, theorem, or mechanism that enforces the constraint |

---

## 3. Actor Claim Map

### 3.1 Compiler and Reuse Pass

| Field | Value |
|-------|-------|
| Actor | Compiler / reuse pass (adversary-controlled) |
| Resource | Alice's value bit $v$ |
| Allowed privilege | **Use** — may synthesize gate operations over the qubit register |
| Forbidden privilege | **Read**, **retain** (outside the intended computation) |
| Observation channel | Gate parameters, wire assignments, measurement outcomes injected by the reuse pass |
| Lifetime | Compilation phase and runtime execution |
| Evidence | Source-access adversary model. In the analyzed five-wire construction, the fifth wire retains $v$ iff $e = b$. This result characterizes the specific modeled circuit; it does not yet bound arbitrary single-ancilla compiler transformations. |

### 3.2 Eve's Signal Measurement (Branch-Conditioning Event)

| Field | Value |
|-------|-------|
| Actor | Eve's projective measurement on $q_2$ (signal wire) |
| Resource | Alice's encoded state $|\psi_v^b\rangle$ |
| Allowed privilege | **Use** — measurement collapses the branch |
| Forbidden privilege | **Read $v$ directly** via a single measurement outcome |
| Observation channel | Classical measurement result $r_E$ |
| Lifetime | Measurement event |
| Evidence | When $e = b$: $r_E$ is correlated with $v$ — partial read is achieved. When $e \neq b$: $r_E$ is uniformly distributed — no read. Characterized precisely by `enumerate_eve_branches`. |

### 3.3 Fifth Wire ($q_4$, Eve's Ancilla)

| Field | Value |
|-------|-------|
| Actor | Fifth wire — workspace qubit allocated by the reuse pass |
| Resource | Alice's value bit $v$ |
| Allowed privilege | **Use** as a workspace qubit |
| Forbidden privilege | **Export** — fifth wire is never transmitted outside the computation |
| Observation channel | Reduced density matrix $\rho_5^{(v,b,e)}$ |
| Lifetime | Post-routing, within the five-wire quantum state |
| Evidence | **Retain** is conditional: $\rho_5 = |v\rangle\langle v|$ when $e = b$ (perfect retain); $\rho_5 = I/2$ when $e \neq b$ (no retain). Verified by `fixed_input_summary()` regression tests. **Export** does not occur: the fifth-wire state is a qubit inside the computation and is never transmitted to any external observer. |

### 3.4 Victim Subsystem ($q_0$–$q_3$, Bob's Observable State)

| Field | Value |
|-------|-------|
| Actor | Bob's measurement on the routed victim subsystem |
| Resource | Alice's intended encoded state $|\psi_v^b\rangle$ |
| Allowed privilege | **Read** — Bob is the authorized recipient |
| Forbidden privilege | **Retain** of a record distinguishing Eve's measurement outcome $r_E$ |
| Observation channel | Victim-subsystem reduced density matrix $\rho_{\text{victim}}$ |
| Lifetime | Post-routing |
| Evidence | Victim fidelity = 1.0 and trace distance = 0 within floating-point precision, per branch, regardless of $r_E$. Verified by `validate_quantum_computation` and `test_analysis.py`. |

### 3.5 Detector (Classical Post-Processing)

| Field | Value |
|-------|-------|
| Actor | Acceptance test applied to Bob's classical result |
| Resource | Bob's outcome $r_B$ (not $v$ directly) |
| Allowed privilege | **Read** of $r_B$; **Export** of the accept/reject bit to protocol output |
| Forbidden privilege | None in current scope (detector is a defined protocol component) |
| Observation channel | Classical: $\mathrm{accept} = (c \neq b) \lor (r_B = v)$ |
| Lifetime | Per protocol round |
| Evidence | Full Boolean truth table generated by `detector_acceptance_truth_table()`. Note: the accept expression takes $v$ as input; whether this constitutes an unintended **read** channel for an external observer depends on the original register reconstruction (open — see Section 8). |

### 3.6 Classical Outputs and Generated Artifacts

| Field | Value |
|-------|-------|
| Actor | `run_analysis` pipeline |
| Resource | Model inputs $(v, b, e, r_E)$ and computed density matrices |
| Allowed privilege | **Export** — outputs are the intended deliverable |
| Forbidden privilege | None (outputs are the purpose of the computation) |
| Observation channel | `run_output/` CSV, JSON, PNG artifacts |
| Lifetime | Run lifetime |
| Evidence | Deterministic output regression test confirms identical artifacts across runs. Contents are explicit model inputs, not unintended side channels. |

---

## 4. Capability Matrix

Each cell shows the privilege status for Alice's value bit $v$.
● = held; – = not held or explicitly forbidden; conditional = depends on
protocol parameters.

| Actor | Use | Read | Retain | Export |
|-------|-----|------|--------|--------|
| Compiler / reuse pass | ● | – (adversarial claim) | – (adversarial claim) | – |
| Eve's signal measurement ($q_2$) | ● | conditional on $e = b$ | – | – |
| Fifth wire ($q_4$) | ● | – (no measurement) | ● iff $e = b$, else – | – |
| Bob's measurement | ● | ● (authorized) | ● (authorized) | – |
| Detector (classical) | – | ● of $r_B$ (not $v$ directly) | ● of accept bit | ● to output |
| `run_analysis` pipeline | – | ● of model inputs | – (single run) | ● to run_output/ |

---

## 5. Threat Model (Revised)

An adversary with privileged compiler and runtime **use** of the qubit register
injects coupled operations into workspace qubits immediately before or after
reuse. The adversary's goal is to **read** and then **retain** Alice's value $v$,
or a quantity correlated with $v$, without causing a statistically
distinguishable change in Bob's observable and without triggering the acceptance
test.

The threat is not a channel-only BB84 intercept. The adversary does not sit on
the quantum channel; it holds **use** privilege over the circuit substrate. The
operative question is whether **use** privilege can be converted to
**read + retain** privilege through injected ancilla operations.

The fifth-wire analysis answers this for the specific five-wire construction: in
that model, **use** converts to **retain** iff $e = b$, and the retained state
is perfectly correlated with $v$ in that case. This result does not yet bound
arbitrary single-ancilla compiler transformations; an adversarial lower bound
remains open. However, **retain** does not become **export** in the five-wire
model, because the ancilla is never transmitted outside the computation. A
realistic adversary would need to arrange **export** through a separate channel —
compilation outputs, logs, calibration artifacts, or a covert classical side
channel — none of which are modeled in the five-wire quantum circuit.

---

## 6. Implemented Evidence

| Claim | Privilege constrained | Test location | Status |
|-------|-----------------------|---------------|--------|
| $\rho_5 = \|v\rangle\langle v\|$ when $e = b$ | **Retain** iff $e = b$ | `analysis.py::fixed_input_summary`, `test_analysis.py` | ✅ verified |
| $\rho_5 = I/2$ when $e \neq b$ | No **retain** when $e \neq b$ | `analysis.py::fixed_input_summary`, `test_analysis.py` | ✅ verified |
| Victim fidelity = 1 per branch | Victim **read** unaffected by $r_E$ | `validate_quantum_computation`, `test_analysis.py` | ✅ verified |
| Qiskit backend reproduces NumPy at $\leq 10^{-10}$ | Implementation correctness | `test_qiskit_parity.py` | ✅ verified |
| Compiler **use** cannot simultaneously **retain** across all $(e, b)$ | **Use** ⊄ **retain** (universally) | Fifth-wire theorem | ✅ claim; adversarial lower bound not yet proven |

---

## 7. Open Claims (Vocabulary for #7 and #14)

**For Issue #7 — victim-channel preservation beyond BB84 inputs**

- **Claim**: The victim subsystem's **read** privilege (Bob's observable) is
  preserved for all input states in the qubit register, not only the four BB84
  states. Concretely: $\rho_{\text{victim}}$ is independent of $r_E$ and
  equal to the target state within numerical precision for arbitrary
  $(\theta, \phi)$ preparation angles.
- **Privilege at stake**: Bob's **read** privilege. The adversary's ancilla
  must not diminish Bob's ability to distinguish the intended input state.
- **Status**: ✅ **Numerically verified over tested pure-state parameterization** —
  `tests/test_parametric_victim.py` establishes preservation across a 60-point
  angle grid and a 200-sample random sweep over
  $(\theta, \phi) \in [0, \pi) \times [0, 2\pi)$ for both Eve bases.
  Qiskit Statevector backend agrees at the same tolerance. Victim fidelity
  $> 1 - 10^{-10}$ on all 200 × 2 branch sets.

  **Scientific scope note**: this is strong numerical evidence over arbitrary
  pure-state preparations, not a formal channel theorem. Sampling over
  $(\theta, \phi)$ does not prove preservation for every input or for states
  entangled with an external reference. The formal follow-up would construct
  a Choi-state (or entangled-reference) test to establish complete channel
  equality rather than sampled-state agreement. Until that test is implemented,
  the correct paper language is: *"Victim preservation was numerically verified
  across the tested continuous pure-state parameterization and independently
  reproduced with Qiskit Statevector simulation."*

**For Issue #14 — malicious compiler model**

- **Claim**: A compiler with **use** privilege cannot construct a single injected
  ancilla that achieves simultaneous **read + retain** of $v$ for all
  $(e, b)$ combinations without disturbing the victim subsystem above a
  detectable threshold.
- **Privilege at stake**: The adversary wants **read + retain**. The fifth-wire
  theorem shows these are not simultaneously achievable across all parameter
  settings for a single ancilla.
- **Status**: ✅ **Prototype implemented** (`src/quantum_reuse/compiler_pass.py`,
  `tests/test_compiler_pass.py`, 75 tests) — the CNOT(q_signal → q_ancilla)
  injection is demonstrated for all four BB84 inputs and a parametric sweep
  of 60 structured + 200 random pure-state inputs.

  Key prototype results:
  - **Victim preserved** in 100% of 260 tested inputs: `|ΔF| < 10⁻¹⁰`.
  - **Z-basis retain**: injected ancilla = `|v⟩⟨v|`; attacker trace distance = 1.
  - **X-basis retain**: injected ancilla = `I/2`; attacker trace distance = 0.
    Without Alice's basis, the ancilla carries no value information.
  - **Privilege label**: `use → retain` (Z-basis: `export_ready`; X-basis:
    `mixed — no value info without basis`).

  **What remains open**: the formal adversarial model bounding the joint
  **read + retain** advantage over *all* single-ancilla injection strategies,
  and the connection to distinguishability bounds. The prototype supplies the
  constructive counterpart; the formal bound is Issue #14's remaining scope.

---

## 8. Detector Gap (Open)

The current acceptance expression is provisional:

$$
\mathrm{accept} = (c \neq b) \lor (r_B = v).
$$

In privilege terms: the detector holds **read** privilege over $r_B$ (Bob's
outcome) but the expression also takes $v$ as a direct input. Whether the
original educational detector held an equivalent **read** privilege over $v$,
or whether it derived $v$ only from $r_B$ and basis information, requires
reconstructing the original detector register. Until that reconstruction is
complete, the exact **read** scope of the detector remains open.

---

## 9. Defensive Directions

- **Cross-layer attestation**: verify the circuit-to-pulse path contains only
  authorized **use** operations on workspace qubits; no injected **read** or
  **retain** events.
- **Complementary-basis and trap-based checks**: statistical evidence that the
  reuse pass has not injected basis-correlated **retain** operations.
- **Least-privilege runtime design**: allocate workspace qubits under a contract
  granting **use** only, with no observable quantum channel to ancilla registers
  outside the authorized operation scope.
- **Export boundary enforcement**: any classical export of ancilla-state
  information must pass through an explicit authorization check before leaving
  the computation boundary.

