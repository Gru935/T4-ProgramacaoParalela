#!/usr/bin/env python3
# Gera as figuras individuais dos slides (maiores, para projecao).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

OUT = os.path.dirname(os.path.abspath(__file__))
SEQ = 93.194233

th      = [1, 2, 4, 8, 16]
p       = [4 * t for t in th]
t_forte = [21.888989, 10.976950, 5.855055, 3.314190, 2.012548]
S_forte = [SEQ / t for t in t_forte]
E_forte = [S / pp for S, pp in zip(S_forte, p)]
t_fraca = [16.594238, 16.339467, 16.879343, 17.745419, 22.178566]
E_fraca = [t_fraca[0] / t for t in t_fraca]

plt.rcParams.update({"font.size": 15, "axes.grid": True, "grid.alpha": 0.35,
                     "axes.axisbelow": True, "figure.autolayout": True})

# --- 1) Escalabilidade FORTE: speed-up x threads ---
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.plot(th, p, "--", color="gray", lw=2, label="Ideal (linear)")
ax.plot(th, S_forte, "o-", color="#1f77b4", lw=2.5, ms=9, label="Híbrido N4 n5")
for x, y in zip(th, S_forte):
    ax.annotate(f"{y:.1f}$\\times$", (x, y), textcoords="offset points",
                xytext=(6, -14), fontsize=12)
ax.set_xscale("log", base=2); ax.set_xticks(th); ax.set_xticklabels(th)
ax.set_xlabel("threads por trabalhador"); ax.set_ylabel("Speed-up (vs sequencial)")
ax.set_title("Escalabilidade forte")
ax.legend(loc="upper left")
fig.savefig(os.path.join(OUT, "fig_forte.pdf")); plt.close(fig)

# --- 2) EFICIENCIA x nucleos (mostra a queda no HT) ---
fig, ax = plt.subplots(figsize=(6.4, 4.2))
colors = ["#2ca02c" if pp <= 32 else "#d62728" for pp in p]
bars = ax.bar([str(pp) for pp in p], E_forte, color=colors, width=0.6)
for r, v in zip(bars, E_forte):
    ax.text(r.get_x() + r.get_width()/2, v + 0.02, f"{v:.2f}", ha="center", fontsize=12)
ax.axvline(3.5, color="black", ls=":", lw=1.5)
ax.text(3.55, 0.15, "  a partir daqui: Hyper-Threading\n  (>1 thread por núcleo físico)",
        fontsize=10, va="bottom")
ax.set_xlabel("núcleos de cálculo (4 trab. $\\times$ threads)")
ax.set_ylabel("Eficiência"); ax.set_ylim(0, 1.2)
ax.set_title("Eficiência: cai quando entra o HT")
fig.savefig(os.path.join(OUT, "fig_efic.pdf")); plt.close(fig)

# --- 3) HIBRIDO x MPI PURA (4 nos) ---
fig, ax = plt.subplots(figsize=(6.4, 4.2))
units = ["32", "64"]
S_hib = [SEQ/3.314190, SEQ/2.012548]
S_mpi = [SEQ/3.203527, SEQ/2.002144]
x = np.arange(2); w = 0.36
ax.bar(x - w/2, S_hib, w, color="#2ca02c", label="Híbrido (threads)")
ax.bar(x + w/2, S_mpi, w, color="#d62728", label="MPI pura (processos)")
for i, (h, m) in enumerate(zip(S_hib, S_mpi)):
    ax.text(i - w/2, h + 0.6, f"{h:.0f}$\\times$", ha="center", fontsize=12)
    ax.text(i + w/2, m + 0.6, f"{m:.0f}$\\times$", ha="center", fontsize=12)
ax.set_xticks(x); ax.set_xticklabels(units)
ax.set_xlabel("unidades de cálculo em 4 nós"); ax.set_ylabel("Speed-up")
ax.set_ylim(0, 56); ax.set_title("Híbrido $\\times$ MPI pura: empate técnico")
ax.legend(loc="upper left")
fig.savefig(os.path.join(OUT, "fig_hibxmpi.pdf")); plt.close(fig)

# --- 4) ALOCACAO DO COORDENADOR (lote controlado, mesmo experimento) ---
fig, ax = plt.subplots(figsize=(6.4, 4.2))
lbl = ["Dedica 1 núcleo\n(n5, nó0=15 th)", "Não dedica\n(n5, nó0=16 th)", "Dedica um nó\n(n4, 3 trab.)"]
val = [2.090397, 2.478364, 4.038376]
bars = ax.bar(lbl, val, color=["#17becf", "#9467bd", "#d62728"], width=0.62)
for r, v in zip(bars, val):
    ax.text(r.get_x() + r.get_width()/2, v + 0.07, f"{v:.2f}s", ha="center", fontsize=12)
ax.annotate("$-$16%", xy=(0, 2.09), xytext=(0, 3.1), ha="center", color="green",
            fontsize=14, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="green", lw=2))
ax.set_ylabel("Tempo (s)"); ax.set_ylim(0, 4.7)
ax.set_title("Alocação do coordenador (4 nós)")
fig.savefig(os.path.join(OUT, "fig_coord.pdf")); plt.close(fig)

# --- 5) Escalabilidade FRACA ---
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.plot(th, t_fraca, "D-", color="#8c564b", lw=2.5, ms=9, label="Híbrido (carga $\\propto$ threads)")
ax.axhline(t_fraca[0], color="gray", ls="--", lw=2, label="Ideal (constante)")
for x_, y_, e in zip(th, t_fraca, E_fraca):
    ax.annotate(f"{y_:.1f}s\n(E={e:.2f})", (x_, y_), textcoords="offset points",
                xytext=(0, 8), fontsize=10, ha="center")
ax.set_xscale("log", base=2); ax.set_xticks(th); ax.set_xticklabels(th)
ax.set_xlabel("threads por trab. (max_iter = 1500$\\times$threads)")
ax.set_ylabel("Tempo (s)"); ax.set_ylim(0, 28)
ax.set_title("Escalabilidade fraca")
ax.legend(loc="upper left")
fig.savefig(os.path.join(OUT, "fig_fraca.pdf")); plt.close(fig)

# --- 6) Render do conjunto de Mandelbrot (ilustracao da capa) ---
W, H = 900, 520
re = np.linspace(-2.5, 1.0, W)
im = np.linspace(-1.0, 1.0, H)
C = re[np.newaxis, :] + 1j * im[:, np.newaxis]
Z = np.zeros_like(C)
div = np.full(C.shape, 200, dtype=float)
for i in range(200):
    Z = Z * Z + C
    newly = (np.abs(Z) > 2) & (div == 200)
    div[newly] = i
fig, ax = plt.subplots(figsize=(7.2, 4.1))
ax.imshow(div, cmap="magma", extent=[-2.5, 1.0, -1.0, 1.0], origin="lower", aspect="auto")
ax.set_xticks([]); ax.set_yticks([])
fig.savefig(os.path.join(OUT, "fig_mandel.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

print("figuras salvas em", OUT)
