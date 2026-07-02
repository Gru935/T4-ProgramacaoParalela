#!/usr/bin/env python3
# Figura do relatorio: comparacao HIBRIDO x MPI PURA (escalabilidade forte e
# fraca em SPEED-UP) + alocacao do coordenador.
#   - Hibrido: dados deste trabalho (max_iter=2000, T_seq=93,19s), -N 4 -n 5,
#     escalando threads -> nucleos de calculo = 4 x threads.
#   - MPI pura: dados do colega (graficos.ods, max_iter=1000, T_seq=76,72s),
#     1..64 processos. Fraca = speed-up escalado (Gustafson): T_seq(carga)/T_par.
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
h_carga = [1500, 3000, 6000, 12000, 24000]                        # fraca (max_iter)
h_tw    = [16.594238, 16.339467, 16.879343, 17.745419, 22.178566]
h_Tseq  = [SEQ_H * c / 2000.0 for c in h_carga]                   # T_seq escalado
h_Sw    = [ts / tw for ts, tw in zip(h_Tseq, h_tw)]               # speed-up fraco

# ---- MPI PURA (max_iter=1000) -- dados do colega (graficos.ods) ----
m_proc  = [1, 4, 8, 16, 32, 64]
m_Sf    = [1, 2.97486, 6.91680, 14.33712, 28.07063, 44.11489]     # forte
m_Ef    = [1, 0.743716, 0.864600, 0.896070, 0.877207, 0.689295]
m_Sw    = [1, 3.07502, 7.22688, 15.45444, 30.34855, 48.47850]     # fraca (speed-up)

plt.rcParams.update({"font.size": 8.5, "axes.grid": True,
                     "grid.alpha": 0.35, "axes.axisbelow": True})
fig, ax = plt.subplots(2, 2, figsize=(8.0, 4.7))
ideal_x = [1, 4, 8, 16, 32, 64]

# (a) FORTE -- speed-up
a = ax[0, 0]
a.plot(ideal_x, ideal_x, "--", color="gray", lw=1, label="Ideal (linear)")
a.plot(h_cores, h_Sf, "o-", color="#2ca02c", label="Híbrido (threads)")
a.plot(m_proc,  m_Sf, "s-", color="#d62728", label="MPI pura (proc.)")
a.set_title("(a) Escalabilidade forte")
a.set_xlabel("unidades de cálculo"); a.set_ylabel("Speed-up")
a.set_xscale("log", base=2); a.set_xticks(ideal_x); a.set_xticklabels(ideal_x)
a.legend(fontsize=7, loc="upper left")

# (b) FRACA -- speed-up escalado (Gustafson)
b = ax[0, 1]
b.plot(ideal_x, ideal_x, "--", color="gray", lw=1, label="Ideal (linear)")
b.plot(h_cores, h_Sw, "o-", color="#2ca02c", label="Híbrido")
b.plot(m_proc,  m_Sw, "s-", color="#d62728", label="MPI pura")
b.set_title("(b) Escalabilidade fraca (speed-up)")
b.set_xlabel("unidades de cálculo"); b.set_ylabel("Speed-up escalado")
b.set_xscale("log", base=2); b.set_xticks(ideal_x); b.set_xticklabels(ideal_x)
b.legend(fontsize=7, loc="upper left")

# (c) Alocacao do coordenador (lote controlado)
c = ax[1, 0]
coord_lbl = ["Dedica\n1 núcleo\n(n5)", "Não dedica\n(n5)", "Dedica\num nó\n(n4)"]
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

# (d) EFICIENCIA forte -- hibrido x MPI pura
d = ax[1, 1]
d.axhline(1.0, color="gray", ls="--", lw=1)
d.plot(h_cores, h_Ef, "o-", color="#2ca02c", label="Híbrido")
d.plot(m_proc,  m_Ef, "s-", color="#d62728", label="MPI pura")
d.set_title("(d) Eficiência (forte)")
d.set_xlabel("unidades de cálculo"); d.set_ylabel("Eficiência")
d.set_xscale("log", base=2); d.set_xticks(ideal_x); d.set_xticklabels(ideal_x)
d.set_ylim(0, 1.25); d.legend(fontsize=7, loc="lower left")

fig.tight_layout(pad=0.5)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graficos.pdf")
fig.savefig(out)
print("salvo:", out, "| hibrido Sw:", [round(x,2) for x in h_Sw])
