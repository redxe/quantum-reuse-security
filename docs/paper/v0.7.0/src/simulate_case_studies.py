from __future__ import annotations

import csv
import math
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures"
DATA.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)


def kron_all(*ops: np.ndarray) -> np.ndarray:
    out = np.array([[1.0 + 0.0j]])
    for op in ops:
        out = np.kron(out, op)
    return out


def basis_bits(index: int, n: int) -> list[int]:
    return [(index >> (n - 1 - q)) & 1 for q in range(n)]


def bits_index(bits: list[int]) -> int:
    idx = 0
    for bit in bits:
        idx = (idx << 1) | bit
    return idx


def controlled_gate(n: int, control: int, target: int, gate: np.ndarray) -> np.ndarray:
    dim = 2**n
    U = np.zeros((dim, dim), dtype=complex)
    for col in range(dim):
        bits = basis_bits(col, n)
        if bits[control] == 0:
            U[col, col] = 1.0
        else:
            target_in = bits[target]
            for target_out in (0, 1):
                out_bits = bits.copy()
                out_bits[target] = target_out
                row = bits_index(out_bits)
                U[row, col] = gate[target_out, target_in]
    return U


def single_gate(n: int, target: int, gate: np.ndarray) -> np.ndarray:
    ops = [I] * n
    ops[target] = gate
    return kron_all(*ops)


def random_qubit(rng: np.random.Generator) -> np.ndarray:
    z = rng.normal(size=2) + 1j * rng.normal(size=2)
    return z / np.linalg.norm(z)


def teleport_cleanup_unitary() -> np.ndarray:
    # Qubit order: source S, ancilla A, destination B.
    U = np.eye(8, dtype=complex)
    gates = [
        single_gate(3, 1, H),
        controlled_gate(3, 1, 2, X),
        controlled_gate(3, 0, 1, X),
        single_gate(3, 0, H),
        controlled_gate(3, 1, 2, X),
        controlled_gate(3, 0, 2, Z),
        single_gate(3, 0, H),
        single_gate(3, 1, H),
    ]
    for gate in gates:
        U = gate @ U
    return U


def test_teleport_cleanup(samples: int = 10_000, seed: int = 314159) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    U = teleport_cleanup_unitary()
    errors = []
    fidelities = []
    for _ in range(samples):
        psi = random_qubit(rng)
        initial = np.kron(psi, np.array([1, 0, 0, 0], dtype=complex))  # |psi> ⊗ |00>
        expected = np.kron(np.array([1, 0, 0, 0], dtype=complex), psi)  # |00> ⊗ |psi>
        actual = U @ initial
        overlap = np.vdot(expected, actual)
        # Correct for any global phase before norm error.
        if abs(overlap) > 0:
            actual = actual * np.exp(-1j * np.angle(overlap))
        errors.append(np.linalg.norm(actual - expected))
        fidelities.append(abs(np.vdot(expected, actual)) ** 2)
    return {
        "samples": float(samples),
        "max_statevector_error": float(max(errors)),
        "mean_statevector_error": float(np.mean(errors)),
        "min_fidelity": float(min(fidelities)),
        "mean_fidelity": float(np.mean(fidelities)),
    }


def bb84_state(value: int, basis: int) -> np.ndarray:
    state = np.array([1.0, 0.0], dtype=complex)
    if value:
        state = X @ state
    if basis:
        state = H @ state
    return state


def sample_measure(state: np.ndarray, basis: int, rng: random.Random) -> int:
    if basis:
        state = H @ state
    probs = np.abs(state) ** 2
    return 0 if rng.random() < probs[0] else 1


def monte_carlo_bb84(shots: int = 1_000_000, seed: int = 271828) -> list[dict[str, float | str]]:
    rng = random.Random(seed)
    counters = {
        "baseline": {"detect": 0, "sifted": 0, "sifted_err": 0, "eve_match": 0, "eve_correct": 0},
        "intercept_resend": {"detect": 0, "sifted": 0, "sifted_err": 0, "eve_match": 0, "eve_correct": 0},
        "source_access": {"detect": 0, "sifted": 0, "sifted_err": 0, "eve_match": 0, "eve_correct": 0},
    }

    for _ in range(shots):
        v = rng.randrange(2)
        b = rng.randrange(2)
        c = rng.randrange(2)
        e = rng.randrange(2)
        signal = bb84_state(v, b)

        # Baseline
        y = sample_measure(signal, c, rng)
        if c == b:
            counters["baseline"]["sifted"] += 1
            if y != v:
                counters["baseline"]["detect"] += 1
                counters["baseline"]["sifted_err"] += 1

        # Intercept and resend
        z = sample_measure(signal, e, rng)
        replacement = bb84_state(z, e)
        y2 = sample_measure(replacement, c, rng)
        if e == b:
            counters["intercept_resend"]["eve_match"] += 1
            counters["intercept_resend"]["eve_correct"] += int(z == v)
        if c == b:
            counters["intercept_resend"]["sifted"] += 1
            if y2 != v:
                counters["intercept_resend"]["detect"] += 1
                counters["intercept_resend"]["sifted_err"] += 1

        # Source access: preparation executed twice; Bob's copy untouched.
        bob_copy = bb84_state(v, b)
        eve_copy = bb84_state(v, b)
        z3 = sample_measure(eve_copy, e, rng)
        y3 = sample_measure(bob_copy, c, rng)
        if e == b:
            counters["source_access"]["eve_match"] += 1
            counters["source_access"]["eve_correct"] += int(z3 == v)
        if c == b:
            counters["source_access"]["sifted"] += 1
            if y3 != v:
                counters["source_access"]["detect"] += 1
                counters["source_access"]["sifted_err"] += 1

    rows = []
    for name, c in counters.items():
        rows.append({
            "variant": name,
            "shots": shots,
            "unconditional_detection_rate": c["detect"] / shots,
            "sifted_qber": c["sifted_err"] / c["sifted"] if c["sifted"] else float("nan"),
            "eve_accuracy_given_basis_match": c["eve_correct"] / c["eve_match"] if c["eve_match"] else float("nan"),
            "eve_basis_match_fraction": c["eve_match"] / shots,
        })
    return rows


def hidden_correlation_curve(points: int = 401) -> list[dict[str, float]]:
    rows = []
    thetas = np.linspace(0.0, math.pi, points)
    for theta in thetas:
        # |psi(theta)> = cos(theta/2)|0> + sin(theta/2)|1> (real meridian).
        a = math.cos(theta / 2)
        b = math.sin(theta / 2)
        # After CNOT to an ancilla and tracing ancilla: diag(|a|^2, |b|^2).
        fidelity = a**4 + b**4
        coherence = 2 * a * b  # baseline <X> for this real state
        attacked_x = 0.0       # dephased reduced state has no off-diagonal terms
        z0_probability = a**2  # unchanged by the attack
        rows.append({
            "theta": float(theta),
            "victim_fidelity": float(fidelity),
            "baseline_x_expectation": float(coherence),
            "attacked_x_expectation": float(attacked_x),
            "z_zero_probability": float(z0_probability),
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def make_plots(curve: list[dict[str, float]], bb84_rows: list[dict]) -> None:
    theta = np.array([r["theta"] for r in curve])
    fidelity = np.array([r["victim_fidelity"] for r in curve])
    baseline_x = np.array([r["baseline_x_expectation"] for r in curve])
    attacked_x = np.array([r["attacked_x_expectation"] for r in curve])

    plt.figure(figsize=(7.2, 4.35))
    plt.plot(theta / math.pi, fidelity, color="#0072B2", linewidth=2.0,
             label="Victim-state fidelity after hidden CNOT")
    plt.plot(theta / math.pi, baseline_x, color="#009E73", linewidth=1.9,
             label="Baseline X expectation")
    plt.plot(theta / math.pi, attacked_x, color="#E69F00", linewidth=1.9,
             linestyle="--", label="Attacked X expectation")
    plt.xlabel(r"Input polar angle $\theta/\pi$")
    plt.ylabel("Value")
    plt.ylim(-0.05, 1.05)
    plt.grid(axis="y", alpha=0.18)
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(FIG / "classical_quantum_leakage_boundary.pdf")
    plt.savefig(FIG / "classical_quantum_leakage_boundary.png", dpi=220)
    plt.close()

    labels = [r["variant"].replace("_", " ") for r in bb84_rows]
    vals = [r["unconditional_detection_rate"] for r in bb84_rows]
    plt.figure(figsize=(6.8, 4.05))
    plt.bar(labels, vals, color=["#0072B2", "#E69F00", "#009E73"],
            edgecolor=["#005680", "#A96E00", "#006E50"], linewidth=0.8)
    plt.ylabel("Unconditional detection rate")
    plt.ylim(0, 0.15)
    plt.grid(axis="y", alpha=0.18)
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.xticks(rotation=12, ha="right")
    plt.tight_layout()
    plt.savefig(FIG / "bb84_detection_rates.pdf")
    plt.savefig(FIG / "bb84_detection_rates.png", dpi=220)
    plt.close()


def main() -> None:
    teleport = test_teleport_cleanup()
    bb84 = monte_carlo_bb84()
    curve = hidden_correlation_curve()

    write_csv(DATA / "teleport_cleanup_results.csv", [teleport])
    write_csv(DATA / "bb84_case_study_results.csv", bb84)
    write_csv(DATA / "hidden_correlation_curve.csv", curve)
    make_plots(curve, bb84)

    print("Teleportation cleanup:")
    for k, v in teleport.items():
        print(f"  {k}: {v}")
    print("\nBB84 case studies:")
    for row in bb84:
        print(row)


if __name__ == "__main__":
    main()
