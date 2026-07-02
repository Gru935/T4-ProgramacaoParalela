#!/usr/bin/env python3
# Figuras dos slides: comparacao HIBRIDO x MPI PURA (forte e fraca em speed-up),
# eficiencia, alocacao do coordenador e render do Mandelbrot.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

OUT = os.path.dirname(os.path.abspath(__file__))
SEQ_H = 93.194233

# HIBRIDO (max_iter=2000)
h_x  = [4, 8, 16, 32, 64]
h_Sf = [SEQ_H/t for t in [21.888989,10.976950,5.855055,3.314190,2.012548]]
h_Ef = [s/c for s, c in zip(h_Sf, h_x)]
h_Sw = [ (SEQ_H*c/2000.0)/tw for c, tw in
         zip([1500,3000,6000,12000,24000],
             [16.594238,16.339467,16.879343,17.745419,22.178566]) ]
# MPI PURA (max_iter=1000) -- dados do colega
m_x  = [1, 4, 8, 16, 32, 64]
m_Sf = [1, 2.97486, 6.91680, 14.33712, 28.07063, 44.11489]
m_Ef = [1, 0.743716, 0.864600, 0.896070, 0.877207, 0.689295]
m_Sw = [1, 3.07502, 7.22688, 15.45444, 30.34855, 48.47850]

plt.rcParams.update({"font.size": 15, "axes.grid": True, "grid.alpha": 0.35,
                     "axes.axisbelow": True, "figure.autolayout": True})
ideal = [1, 4, 8, 16, 32, 64]

def scaling_fig(fname, yh, ym, title, ylab):
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.plot(ideal, ideal, "--", color="gray", lw=2, label="Ideal (linear)")
    ax.plot(h_x, yh, "o-", color="#2ca02c", lw=2.5, ms=9, label="Híbrido")
    ax.plot(m_x, ym, "s-", color="#d62728", lw=2.5, ms=8, label="MPI pura")
    ax.set_xscale("log", base=2); ax.set_xticks(ideal); ax.set_xticklabels(ideal)
    ax.set_xlabel("unidades de cálculo"); ax.set_ylabel(ylab)
    ax.set_title(title); ax.legend(loc="upper left", fontsize=13)
    fig.savefig(os.path.join(OUT, fname)); plt.close(fig)

scaling_fig("fig_forte.pdf", h_Sf, m_Sf, "Escalabilidade forte", "Speed-up")
scaling_fig("fig_fraca.pdf", h_Sw, m_Sw, "Escalabilidade fraca (speed-up)", "Speed-up escalado")

# Eficiencia (forte) -- hibrido x MPI pura, marcando o HT
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.axhline(1.0, color="gray", ls="--", lw=1.5)
ax.plot(h_x, h_Ef, "o-", color="#2ca02c", lw=2.5, ms=9, label="Híbrido")
ax.plot(m_x, m_Ef, "s-", color="#d62728", lw=2.5, ms=8, label="MPI pura")
ax.axvspan(45, 70, color="red", alpha=0.08)
ax.text(64, 0.5, "HT", ha="center", fontsize=13, color="red")
ax.set_xscale("log", base=2); ax.set_xticks(ideal); ax.set_xticklabels(ideal)
ax.set_xlabel("unidades de cálculo"); ax.set_ylabel("Eficiência")
ax.set_title("Eficiência: cai quando entra o HT"); ax.set_ylim(0, 1.25)
ax.legend(loc="lower left", fontsize=13)
fig.savefig(os.path.join(OUT, "fig_efic.pdf")); plt.close(fig)

# Alocacao do coordenador (lote controlado)
fig, ax = plt.subplots(figsize=(6.4, 4.2))
lbl = ["Dedica 1 núcleo\n(n5, nó0=15 th)", "Não dedica\n(n5, nó0=16 th)", "Dedica um nó\n(n4, 3 trab.)"]
val = [2.090397, 2.478364, 4.038376]
bars = ax.bar(lbl, val, color=["#17becf", "#9467bd", "#d62728"], width=0.62)
for r, v in zip(bars, val):
    ax.text(r.get_x()+r.get_width()/2, v+0.07, f"{v:.2f}s", ha="center", fontsize=12)
ax.annotate("$-$16%", xy=(0, 2.09), xytext=(0, 3.1), ha="center", color="green",
            fontsize=14, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="green", lw=2))
ax.set_ylabel("Tempo (s)"); ax.set_ylim(0, 4.7)
ax.set_title("Alocação do coordenador (4 nós)")
fig.savefig(os.path.join(OUT, "fig_coord.pdf")); plt.close(fig)

# Render do Mandelbrot (capa)
W, H = 900, 520
re = np.linspace(-2.5, 1.0, W); im = np.linspace(-1.0, 1.0, H)
C = re[np.newaxis, :] + 1j*im[:, np.newaxis]
Z = np.zeros_like(C); div = np.full(C.shape, 200, dtype=float)
for i in range(200):
    Z = Z*Z + C
    newly = (np.abs(Z) > 2) & (div == 200); div[newly] = i
fig, ax = plt.subplots(figsize=(7.2, 4.1))
ax.imshow(div, cmap="magma", extent=[-2.5,1.0,-1.0,1.0], origin="lower", aspect="auto")
ax.set_xticks([]); ax.set_yticks([])
fig.savefig(os.path.join(OUT, "fig_mandel.png"), dpi=150, bbox_inches="tight"); plt.close(fig)

print("figuras dos slides salvas em", OUT)
