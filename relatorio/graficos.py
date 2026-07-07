#!/usr/bin/env python3
# Figura do relatorio (mesma linha dos slides): comparacao HIBRIDO x MPI PURA na
# escalabilidade FORTE (speed-up + eficiencia) + alocacao do coordenador.
#   - Hibrido: dados deste trabalho (max_iter=2000, T_seq=93,19s), -N 4 -n 5,
#     escalando threads -> unidades de calculo = 4 x threads.
#   - MPI pura: dados do colega (graficos.ods, max_iter=1000, T_seq=76,72s),
#     1..64 processos. Compara-se pelas metricas (speed-up/eficiencia).
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

SEQ_H = 93.194233   # T(1) hibrido (max_iter=2000)

# ---- HIBRIDO (max_iter=2000) ----
h_cores = [4, 8, 16, 32, 64]
h_tf    = [21.888989, 10.976950, 5.855055, 3.314190, 2.012548]   # forte
h_Sf    = [SEQ_H / t for t in h_tf]
h_Ef    = [s / c for s, c in zip(h_Sf, h_cores)]

# ---- MPI PURA (max_iter=1000) -- dados do colega (graficos.ods) ----
m_proc  = [1, 4, 8, 16, 32, 64]
m_Sf    = [1, 2.97486, 6.91680, 14.33712, 28.07063, 44.11489]     # forte
m_Ef    = [1, 0.743716, 0.864600, 0.896070, 0.877207, 0.689295]

plt.rcParams.update({"font.size": 8.5, "axes.grid": True,
                     "grid.alpha": 0.35, "axes.axisbelow": True})
fig, ax = plt.subplots(1, 3, figsize=(9.8, 3.0))
ideal_x = [1, 4, 8, 16, 32, 64]

# (a) FORTE -- speed-up
a = ax[0]
a.plot(ideal_x, ideal_x, "--", color="gray", lw=1, label="Ideal (linear)")
a.plot(h_cores, h_Sf, "o-", color="#2ca02c", label="Híbrido (threads)")
a.plot(m_proc,  m_Sf, "s-", color="#d62728", label="MPI pura (proc.)")
a.set_title("(a) Escalabilidade forte")
a.set_xlabel("unidades de cálculo"); a.set_ylabel("Speed-up")
a.set_xscale("log", base=2); a.set_xticks(ideal_x); a.set_xticklabels(ideal_x)
a.legend(fontsize=7, loc="upper left")

# (b) EFICIENCIA forte -- hibrido x MPI pura
b = ax[1]
b.axhline(1.0, color="gray", ls="--", lw=1)
b.plot(h_cores, h_Ef, "o-", color="#2ca02c", label="Híbrido")
b.plot(m_proc,  m_Ef, "s-", color="#d62728", label="MPI pura")
b.set_title("(b) Eficiência (forte)")
b.set_xlabel("unidades de cálculo"); b.set_ylabel("Eficiência")
b.set_xscale("log", base=2); b.set_xticks(ideal_x); b.set_xticklabels(ideal_x)
b.set_ylim(0, 1.25); b.legend(fontsize=7, loc="lower left")

# (c) Alocacao do coordenador (lote controlado)
c = ax[2]
coord_lbl = ["Dedica\n1 núcleo\n(n5)", "Não\ndedica\n(n5)", "Dedica\num nó\n(n4)"]
coord_t   = [2.090397, 2.478364, 4.038376]
coord_col = ["#17becf", "#9467bd", "#d62728"]
bars = c.bar(coord_lbl, coord_t, color=coord_col, width=0.62)
for r, v in zip(bars, coord_t):
    c.text(r.get_x() + r.get_width()/2, v + 0.06, f"{v:.2f}s", ha="center", fontsize=8)
c.set_title("(c) Alocação do coordenador")
c.set_ylabel("Tempo (s)"); c.set_ylim(0, 4.7)
c.annotate("$-$16%", xy=(0, 2.09), xytext=(0, 3.1), ha="center", color="green",
           fontsize=8.5, fontweight="bold",
           arrowprops=dict(arrowstyle="->", color="green", lw=1.2))

fig.tight_layout(pad=0.5)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficos.pdf")
fig.savefig(out)
print("salvo:", out, "| hibrido Sf:", [round(x, 2) for x in h_Sf],
      "| hibrido Ef:", [round(x, 2) for x in h_Ef])
