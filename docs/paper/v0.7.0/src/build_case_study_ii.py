from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
DATA = ROOT / "data"
FIG.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

# Complete five-wire output amplitudes supplied by the author from Quirk.
# Quirk groups the first 16 amplitudes and the second 16 amplitudes by the
# fifth exported wire. The 16-entry index within each block labels the four
# wires shown by the final Amps4 display.
BASELINE = np.array([
    0.3535533547401428, 0.0, 0.2499999701976776, 0.2499999701976776,
    0.0, 0.3535533547401428, 0.2499999701976776, -0.2499999701976776,
    0.2499999701976776, 0.2499999701976776, 0.3535533547401428, 0.0,
    0.2499999701976776, -0.2499999701976776, 0.0, 0.3535533547401428,
    *([0.0] * 16),
], dtype=complex)

INTERCEPT_RESEND = np.array([
    0.1767766773700714, 0.1767766773700714, 0.2499999701976776, 0.0,
    0.1767766773700714, 0.1767766773700714, 0.2499999701976776, 0.0,
    0.2499999701976776, 0.2499999701976776, 0.3535533547401428, 0.0,
    0.0, 0.0, 0.0, 0.0,
    0.1767766773700714, -0.1767766773700714, 0.0, 0.2499999701976776,
    0.1767766773700714, -0.1767766773700714, 0.0, 0.2499999701976776,
    0.2499999701976776, -0.2499999701976776, 0.0, 0.3535533547401428,
    0.0, 0.0, 0.0, 0.0,
], dtype=complex)

ADVANCED = np.array([
    0.2499999701976776, 0.0, 0.2499999701976776, 0.0,
    0.0, 0.2499999701976776, 0.2499999701976776, 0.0,
    0.1767766773700714, 0.1767766773700714, 0.3535533547401428, 0.0,
    0.1767766773700714, -0.1767766773700714, 0.0, 0.0,
    0.2499999701976776, 0.0, 0.0, 0.2499999701976776,
    0.0, -0.2499999701976776, 0.0, -0.2499999701976776,
    0.1767766773700714, -0.1767766773700714, 0.0, 0.0,
    0.1767766773700714, 0.1767766773700714, 0.0, 0.3535533547401428,
], dtype=complex)

QUIRK_COHERENCE = {
    "baseline": 0.9999999523962775,
    "intercept_resend": 0.49999997619813874,
    "advanced": 0.49999997619813874,
}

# Machine-readable column definitions supplied by the author. Identity-note
# blocks and displays are retained here for provenance, but are omitted from
# operational circuit diagrams.
CIRCUITS = {
    "baseline": [
        ["inputA3"], ["H", "H"], ["Measure", "Measure"],
        ["Measure", "Measure"], ["•", 1, "X"], [1, "•", "H"],
        ["Amps3"], [], [1, 1, "inputB3"], [1, 1, "Bloch", "H"],
        [1, 1, "Density", "Measure"], [1, 1, "H", "•"],
        [1, 1, "Measure"], ["Amps4"],
    ],
    "intercept_resend": [
        ["inputA3"], ["H", "H"], ["Measure", "Measure"], ["Chance2"],
        ["•", 1, "X"], [1, "•", "H"], [1, 1, "inputR2"],
        [1, 1, "H", "H"], [1, 1, "Measure", "X"],
        [1, 1, 1, "Swap", "Swap"], [1, 1, "Swap", 1, "Swap"],
        [1, 1, "inputB3"], [1, 1, 1, "H"], [1, 1, 1, "Measure"],
        [1, 1, "H", "•"], [1, 1, "Measure"], ["Amps4"],
    ],
    "advanced": [
        ["inputA3"], ["H", "H"], ["Measure", "Measure"],
        ["•", 1, 1, "X"], [1, "•", 1, "H"],
        ["Measure", "Measure"], ["•", 1, "X"], [1, "•", "H"],
        [1, 1, "inputR2"], [1, 1, "H"], [1, 1, "Measure"],
        [1, 1, 1, "Swap", "Swap"], [1, 1, "Swap", 1, "Swap"],
        [1, 1, "inputB3"], [1, 1, 1, "H"], [1, 1, 1, "Measure"],
        [1, 1, "H", "•"], [1, 1, "Measure"], ["Amps4"],
    ],
}


def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def reduced_display(v: np.ndarray) -> np.ndarray:
    """Trace out the fifth wire from a Quirk 32-amplitude export."""
    m = normalize(v).reshape(2, 16)
    return m.T @ m.conj()


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(rho)
    return float(-sum(x * math.log2(x) for x in vals if x > 1e-14))


def pure_fidelity(psi: np.ndarray, rho: np.ndarray) -> float:
    return float(np.real(np.vdot(psi, rho @ psi)))


def trace_distance(rho: np.ndarray, sigma: np.ndarray) -> float:
    vals = np.linalg.eigvalsh(rho - sigma)
    return 0.5 * float(np.sum(np.abs(vals)))


def total_variation(p: np.ndarray, q: np.ndarray) -> float:
    return 0.5 * float(np.sum(np.abs(p - q)))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_circuit_tex() -> str:
    # A deliberately literal reconstruction. The two consecutive Measure
    # columns in the baseline are retained. Controlled-H gates are drawn with
    # the control connected to the H target. The two SWAP operations are placed
    # in separate columns with a visual spacer so their lines cannot overlap.
    return r"""
\begin{figure}[tbp]
\centering
\begin{adjustbox}{max width=\textwidth}
\begin{quantikz}[row sep=0.34cm,column sep=0.30cm]
\lstick{$q_0$} & \gate{H} & \meter{} & \meter{} & \ctrl{2} & \qw      & \slice[style={black,dashed},label style={black}]{Alice checkpoint} \qw & \qw      & \qw      & \qw       & \qw \\
\lstick{$q_1$} & \gate{H} & \meter{} & \meter{} & \qw      & \ctrl{1} & \qw & \qw      & \qw      & \qw       & \qw \\
\lstick{$q_2$} & \qw      & \qw      & \qw      & \targ{}  & \gate{H} & \qw & \qw      & \qw      & \gate{H}  & \meter{} \\
\lstick{$q_3$} & \qw      & \qw      & \qw      & \qw      & \qw      & \qw & \gate{H} & \meter{} & \ctrl{-1} & \qw \\
\lstick{$q_4$} & \qw      & \qw      & \qw      & \qw      & \qw      & \qw & \qw      & \qw      & \qw       & \qw
\end{quantikz}
\end{adjustbox}
\caption{Baseline circuit reconstructed literally from the supplied column
array. The two consecutive measurements on $q_0$ and $q_1$ are both present in
the export and are therefore both shown. The control on $q_1$ acts on a
Hadamard target on $q_2$; later, the measured value on $q_3$ controls a second
Hadamard on $q_2$. Display widgets and identity annotation blocks are omitted.}
\label{fig:caseii-baseline-circuit}
\end{figure}

\begin{figure}[tbp]
\centering
\begin{adjustbox}{max width=\textwidth}
\begin{quantikz}[row sep=0.34cm,column sep=0.31cm]
\lstick{$q_0$} & \gate{H} & \meter{} & \ctrl{2} & \qw      & \slice[style={black,dashed},label style={black}]{Alice} \qw & \qw      & \qw      & \qw      & \qw      & \qw      & \slice[style={black,dashed},label style={black}]{routing} \qw & \qw      & \qw      & \qw       & \qw \\
\lstick{$q_1$} & \gate{H} & \meter{} & \qw      & \ctrl{1} & \qw & \qw      & \qw      & \qw      & \qw      & \qw      & \qw & \qw      & \qw      & \qw       & \qw \\
\lstick{$q_2$} & \qw      & \qw      & \targ{}  & \gate{H} & \qw & \gate{H} & \meter{} & \qw      & \qw      & \swap{2} & \qw & \qw      & \qw      & \gate{H}  & \meter{} \\
\lstick{$q_3$} & \qw      & \qw      & \qw      & \qw      & \qw & \gate{H} & \gate{X} & \swap{1} & \qw      & \qw      & \qw & \gate{H} & \meter{} & \ctrl{-1} & \qw \\
\lstick{$q_4$} & \qw      & \qw      & \qw      & \qw      & \qw & \qw      & \qw      & \targX{} & \qw      & \targX{} & \qw & \qw      & \qw      & \qw       & \qw
\end{quantikz}
\end{adjustbox}
\caption{Ordinary intercept--resend circuit. The routing is the ordered pair
$\operatorname{SWAP}(q_3,q_4)$ followed by
$\operatorname{SWAP}(q_2,q_4)$. The operations occupy separate columns, with a
visual spacer between them, so the SWAP lines remain distinct. The $H$ on
$q_2$ controlled by $q_3$ is drawn explicitly near the end of the circuit.}
\label{fig:caseii-intercept-circuit}
\end{figure}

\begin{figure}[tbp]
\centering
\begin{adjustbox}{max width=\textwidth}
\begin{quantikz}[row sep=0.34cm,column sep=0.27cm]
\lstick{$q_0$} & \gate{H} & \meter{} & \ctrl{3} & \qw      & \meter{} & \ctrl{2} & \qw      & \slice[style={black,dashed},label style={black}]{Alice} \qw & \qw      & \qw      & \qw      & \qw      & \qw      & \slice[style={black,dashed},label style={black}]{routing} \qw & \qw      & \qw      & \qw       & \qw \\
\lstick{$q_1$} & \gate{H} & \meter{} & \qw      & \ctrl{2} & \meter{} & \qw      & \ctrl{1} & \qw & \qw      & \qw      & \qw      & \qw      & \qw      & \qw & \qw      & \qw      & \qw       & \qw \\
\lstick{$q_2$} & \qw      & \qw      & \qw      & \qw      & \qw      & \targ{}  & \gate{H} & \qw & \gate{H} & \meter{} & \qw      & \qw      & \swap{2} & \qw & \qw      & \qw      & \gate{H}  & \meter{} \\
\lstick{$q_3$} & \qw      & \qw      & \targ{}  & \gate{H} & \qw      & \qw      & \qw      & \qw & \qw      & \qw      & \swap{1} & \qw      & \qw      & \qw & \gate{H} & \meter{} & \ctrl{-1} & \qw \\
\lstick{$q_4$} & \qw      & \qw      & \qw      & \qw      & \qw      & \qw      & \qw      & \qw & \qw      & \qw      & \targX{} & \qw      & \targX{} & \qw & \qw      & \qw      & \qw       & \qw
\end{quantikz}
\end{adjustbox}
\caption{Advanced source-access circuit. Alice's measured selectors first
control preparation operations on $q_3$, are measured again exactly as in the
export, and then control a second preparation on $q_2$. The ordered SWAP pair is
again drawn in separate columns. This figure represents the supplied gate
order without using the original Quirk screenshot.}
\label{fig:caseii-advanced-circuit}
\end{figure}
"""


def probability_panel_tex(diagonals: dict[str, np.ndarray]) -> str:
    titles = {
        "baseline": "Baseline",
        "intercept_resend": "Intercept--resend",
        "advanced": "Advanced source access",
    }
    chunks = [
        r"\begin{tikzpicture}",
        r"\begin{groupplot}[",
        r"group style={group size=1 by 3,vertical sep=0.82cm},",
        r"width=0.92\textwidth,height=0.185\textwidth,",
        r"xmin=-0.7,xmax=15.7,ymin=0,ymax=0.14,",
        r"ytick={0,0.0625,0.125},yticklabels={$0$,$1/16$,$1/8$},",
        r"ylabel={probability},",
        r"axis line style={black!65},tick style={black!65},",
        r"title style={font=\small\bfseries},",
        r"grid=major,grid style={black!10},",
        r"]",
    ]
    labels = r"{$0000$,$0001$,$0010$,$0011$,$0100$,$0101$,$0110$,$0111$,$1000$,$1001$,$1010$,$1011$,$1100$,$1101$,$1110$,$1111$}"
    for idx, key in enumerate(("baseline", "intercept_resend", "advanced")):
        if idx < 2:
            opts = f"title={{{titles[key]}}},xtick=\\empty"
        else:
            opts = (
                f"title={{{titles[key]}}},xtick={{0,1,...,15}},"
                f"xticklabels={labels},"
                r"x tick label style={rotate=55,anchor=east,font=\scriptsize},"
                r"xlabel={display-register basis state}"
            )
        chunks.append(fr"\nextgroupplot[{opts}]")
        coords = " ".join(f"({i},{float(p):.12g})" for i, p in enumerate(diagonals[key]))
        color = {"baseline": "BaselineBlue", "intercept_resend": "InterceptOrange", "advanced": "AdvancedTeal"}[key]
        chunks.append(fr"\addplot[ybar,bar width=4.2pt,fill={color}!78,draw={color}!95!black] coordinates {{{coords}}};")
    chunks.extend([r"\end{groupplot}", r"\end{tikzpicture}"])
    return "\n".join(chunks)


def branch_amplitude_tex(vectors: dict[str, np.ndarray]) -> str:
    titles = {
        "baseline": "Baseline",
        "intercept_resend": "Intercept--resend",
        "advanced": "Advanced source access",
    }
    chunks = [
        r"\begin{tikzpicture}",
        r"\begin{groupplot}[",
        r"group style={group size=1 by 3,vertical sep=0.82cm},",
        r"width=0.92\textwidth,height=0.185\textwidth,",
        r"xmin=-0.7,xmax=15.7,ymin=-0.39,ymax=0.39,",
        r"ytick={-0.353553,0,0.353553},",
        r"yticklabels={$-1/(2\sqrt2)$,$0$,$1/(2\sqrt2)$},",
        r"ylabel={real amplitude},",
        r"axis line style={black!65},tick style={black!65},",
        r"title style={font=\small\bfseries},",
        r"grid=major,grid style={black!10},",
        r"]",
    ]
    labels = r"{$0000$,$0001$,$0010$,$0011$,$0100$,$0101$,$0110$,$0111$,$1000$,$1001$,$1010$,$1011$,$1100$,$1101$,$1110$,$1111$}"
    for idx, key in enumerate(("baseline", "intercept_resend", "advanced")):
        if idx < 2:
            opts = f"title={{{titles[key]}}},xtick=\\empty"
        else:
            opts = (
                f"title={{{titles[key]}}},xtick={{0,1,...,15}},"
                f"xticklabels={labels},"
                r"x tick label style={rotate=55,anchor=east,font=\scriptsize},"
                r"xlabel={display-register basis state}"
            )
        chunks.append(fr"\nextgroupplot[{opts}]")
        m = normalize(vectors[key]).reshape(2, 16)
        c0 = " ".join(f"({i-0.14},{float(m[0,i].real):.12g})" for i in range(16))
        c1 = " ".join(f"({i+0.14},{float(m[1,i].real):.12g})" for i in range(16))
        color = {"baseline": "BaselineBlue", "intercept_resend": "InterceptOrange", "advanced": "AdvancedTeal"}[key]
        chunks.append(fr"\addplot[ybar,bar width=2.2pt,fill={color}!82,draw={color}!95!black] coordinates {{{c0}}};")
        chunks.append(fr"\addplot[ybar,bar width=2.2pt,fill={color}!22,draw={color}!95!black,postaction={{pattern=north east lines,pattern color={color}!80!black}}] coordinates {{{c1}}};")
    chunks.extend([r"\end{groupplot}", r"\end{tikzpicture}"])
    return "\n".join(chunks)


def density_tex(rhos: dict[str, np.ndarray]) -> str:
    max_abs = max(float(np.max(np.abs(np.real(r)))) for r in rhos.values())
    titles = {
        "baseline": r"Baseline $\rho_0$",
        "intercept_resend": r"Intercept--resend $\rho_I$",
        "advanced": r"Advanced $\rho_A$",
    }
    chunks = [r"\begin{tikzpicture}[x=0.255cm,y=0.255cm,font=\scriptsize]"]
    for panel, key in enumerate(("baseline", "intercept_resend", "advanced")):
        rho = rhos[key]
        xshift = panel * 5.35
        chunks.append(fr"\begin{{scope}}[xshift={xshift}cm]")
        chunks.append(fr"\node[font=\small\bfseries] at (7.5,1.3) {{{titles[key]}}};")
        for i in range(16):
            for j in range(16):
                val = float(np.real(rho[i, j]))
                if abs(val) < 1e-11:
                    fill = "white"
                    border = "black!15"
                else:
                    pct = max(8, min(88, round(abs(val) / max_abs * 88)))
                    if val > 0:
                        fill = f"BaselineBlue!{pct}"
                        border = "BaselineBlue!45!black"
                    else:
                        fill = f"InterceptOrange!{pct}"
                        border = "InterceptOrange!55!black"
                chunks.append(
                    fr"\filldraw[fill={fill},draw={border},line width=0.08pt] "
                    fr"({j},{-i}) rectangle ++(1,-1);"
                )
        for tick in (0, 4, 8, 12, 15):
            chunks.append(fr"\node[anchor=north] at ({tick + 0.5},-16.15) {{{tick}}};")
            chunks.append(fr"\node[anchor=east] at (-0.15,{-tick - 0.5}) {{{tick}}};")
        chunks.append(r"\node[anchor=north] at (8,-17.15) {column};")
        chunks.append(r"\node[rotate=90] at (-1.15,-8) {row};")
        chunks.append(r"\end{scope}")
    chunks.append(r"\end{tikzpicture}")
    return "\n".join(chunks)


def main() -> None:
    vectors = {
        "baseline": BASELINE,
        "intercept_resend": INTERCEPT_RESEND,
        "advanced": ADVANCED,
    }
    rhos = {name: reduced_display(v) for name, v in vectors.items()}
    diagonals = {name: np.real(np.diag(rho)) for name, rho in rhos.items()}

    baseline_psi = normalize(BASELINE)[:16]
    baseline_psi = normalize(baseline_psi)
    rho0 = rhos["baseline"]
    metrics = []
    for name, rho in rhos.items():
        td = trace_distance(rho0, rho)
        metrics.append({
            "variant": name,
            "quirk_coherence": QUIRK_COHERENCE[name],
            "purity": purity(rho),
            "entropy_bits": entropy(rho),
            "fidelity_with_baseline": pure_fidelity(baseline_psi, rho),
            "trace_distance_from_baseline": td,
            "helstrom_success_equal_prior": (1 + td) / 2,
            "z_basis_total_variation": total_variation(diagonals["baseline"], diagonals[name]),
        })

    write_csv(DATA / "case_study_ii_exact_metrics.csv", metrics)
    with (DATA / "case_study_ii_circuit_columns.json").open("w", encoding="utf-8") as f:
        json.dump(CIRCUITS, f, indent=2)
    with (DATA / "case_study_ii_output_amplitudes.json").open("w", encoding="utf-8") as f:
        json.dump({k: [[float(z.real), float(z.imag)] for z in v] for k, v in vectors.items()}, f, indent=2)

    (FIG / "case_study_ii_circuits.tex").write_text(build_circuit_tex(), encoding="utf-8")
    (FIG / "case_study_ii_probability_densities.tex").write_text(probability_panel_tex(diagonals), encoding="utf-8")
    (FIG / "case_study_ii_branch_amplitudes.tex").write_text(branch_amplitude_tex(vectors), encoding="utf-8")
    (FIG / "case_study_ii_density_matrices.tex").write_text(density_tex(rhos), encoding="utf-8")

    print("Case Study II metrics")
    for row in metrics:
        print(row)


if __name__ == "__main__":
    main()
