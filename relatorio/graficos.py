#!/usr/bin/env python3
# Gera relatorio/graficos.pdf a partir dos dados de results_t4.csv.
# Metodologia do professor: hibrido SEMPRE em -N 4 -n 5 (1 coordenador + 4
# trabalhadores, coordenador compartilhando o no), escalando por THREADS.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

SEQ = 93.194233

# --- Escalabilidade FORTE: hibrido N4 n5, max_iter=2000, variando threads ---
th      = [1, 2, 4, 8, 16]
t_forte = [21.888989, 10.976950, 5.855055, 3.314190, 2.012548]
p_forte = [4 * t for t in th]                 # 4 trabalhadores x threads
S_forte = [SEQ / t for t in t_forte]
ideal_S = p_forte                             # speed-up ideal = nº de cores

# --- Hibrido x MPI pura, em 4 nos (mesma quantidade de unidades de calculo) ---
units    = [32, 64]
S_hib_c  = [SEQ / 3.314190, SEQ / 2.012548]   # hibrido: 8 e 16 threads/worker
S_mpi_c  = [SEQ / 3.203527, SEQ / 2.002144]   # MPI pura: 32 e 64 processos

# --- Alocacao do coordenador (4 nos; lote controlado, mesmo experimento) ---
# n5 = coordenador compartilha o no 0; nucleo = worker do no 0 usa 15 threads
# (1 core dedicado ao coordenador). n4 = coordenador ocupa um no inteiro.
coord_lbl = ["Dedica\n1 núcleo\n(n5)", "Não dedica\n(n5)", "Dedica\num nó\n(n4)"]
coord_t   = [2.090397, 2.478364, 4.038376]
coord_col = ["#17becf", "#9467bd", "#d62728"]

# --- Escalabilidade FRACA: N4 n5, carga proporcional as threads ---
t_fraca = [16.594238, 16.339467, 16.879343, 17.745419, 22.178566]

plt.rcParams.update({"font.size": 8.5, "axes.grid": True,
                     "grid.alpha": 0.35, "axes.axisbelow": True})
fig, ax = plt.subplots(2, 2, figsize=(8.0, 4.5))

# (a) FORTE: speed-up x threads (N4 n5)
a = ax[0, 0]
a.plot(th, ideal_S, "--", color="gray", label="Ideal (4$\\times$threads)")
a.plot(th, S_forte, "o-", color="#1f77b4", label="Híbrido N4 n5")
for x, y in zip(th, S_forte):
    a.annotate(f"{y:.0f}$\\times$", (x, y), textcoords="offset points",
               xytext=(4, -9), fontsize=7)
a.set_title("(a) Escalabilidade forte (N4 n5, max\\_iter=2000)")
a.set_xlabel("threads por trabalhador"); a.set_ylabel("Speed-up (vs sequencial)")
a.set_xscale("log", base=2); a.set_xticks(th); a.set_xticklabels(th)
a.legend(fontsize=7.5, loc="upper left")

# (b) Hibrido x MPI pura (4 nos)
b = ax[0, 1]
x = np.arange(len(units)); w = 0.38
b.bar(x - w/2, S_hib_c, w, color="#2ca02c", label="Híbrido (N4 n5, threads)")
b.bar(x + w/2, S_mpi_c, w, color="#d62728", label="MPI pura (processos)")
for i, (h, m) in enumerate(zip(S_hib_c, S_mpi_c)):
    b.text(i - w/2, h + 0.6, f"{h:.0f}", ha="center", fontsize=7)
    b.text(i + w/2, m + 0.6, f"{m:.0f}", ha="center", fontsize=7)
b.set_title("(b) Híbrido $\\times$ MPI pura (4 nós)")
b.set_xlabel("unidades de cálculo (threads / processos)"); b.set_ylabel("Speed-up")
b.set_xticks(x); b.set_xticklabels(["32", "64"]); b.set_ylim(0, 56)
b.legend(fontsize=7.5, loc="upper left")

# (c) Alocacao do coordenador (dedicar 1 nucleo vs nao vs dedicar um no)
c = ax[1, 0]
bars = c.bar(coord_lbl, coord_t, color=coord_col, width=0.62)
for r, v in zip(bars, coord_t):
    c.text(r.get_x() + r.get_width()/2, v + 0.06, f"{v:.2f}s", ha="center", fontsize=8)
c.set_title("(c) Alocação do coordenador")
c.set_ylabel("Tempo (s)"); c.set_ylim(0, 4.7)
c.annotate("$-$16%", xy=(0, 2.09), xytext=(0, 3.1), ha="center", color="green",
           fontsize=8.5, fontweight="bold",
           arrowprops=dict(arrowstyle="->", color="green", lw=1.2))

# (d) FRACA: tempo x threads (N4 n5, carga proporcional)
d = ax[1, 1]
d.plot(th, t_fraca, "D-", color="#8c564b", label="Híbrido (carga $\\propto$ threads)")
d.axhline(t_fraca[0], color="gray", ls="--", lw=1, label="Ideal (constante)")
for x_, y_ in zip(th, t_fraca):
    d.annotate(f"{y_:.1f}s", (x_, y_), textcoords="offset points", xytext=(0, 6), fontsize=7)
d.set_title("(d) Escalabilidade fraca (N4 n5)")
d.set_xlabel("threads por trab. (max\\_iter = 1500$\\times$threads)")
d.set_ylabel("Tempo (s)")
d.set_xscale("log", base=2); d.set_xticks(th); d.set_xticklabels(th)
d.set_ylim(0, 26); d.legend(fontsize=7.5, loc="upper left")

fig.tight_layout(pad=0.5)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficos.pdf")
fig.savefig(out)
print("salvo:", out)
