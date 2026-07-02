#!/usr/bin/env python3
# Figura dos SLIDES (sem o painel do coordenador): forte, fraca e eficiencia.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

OUT = os.path.dirname(os.path.abspath(__file__))
SEQ_H = 93.194233

h_x  = [4, 8, 16, 32, 64]
h_Sf = [SEQ_H/t for t in [21.888989, 10.976950, 5.855055, 3.314190, 2.012548]]
h_Ef = [s/c for s, c in zip(h_Sf, h_x)]
h_Sw = [(SEQ_H*c/2000.0)/tw for c, tw in
        zip([1500, 3000, 6000, 12000, 24000],
            [16.594238, 16.339467, 16.879343, 17.745419, 22.178566])]
m_x  = [1, 4, 8, 16, 32, 64]
m_Sf = [1, 2.97486, 6.91680, 14.33712, 28.07063, 44.11489]
m_Ef = [1, 0.743716, 0.864600, 0.896070, 0.877207, 0.689295]
m_Sw = [1, 3.07502, 7.22688, 15.45444, 30.34855, 48.47850]

plt.rcParams.update({"font.size": 9, "axes.grid": True, "grid.alpha": 0.35,
                     "axes.axisbelow": True})
ideal = [1, 4, 8, 16, 32, 64]

fig = plt.figure(figsize=(7.4, 5.0))
gs = fig.add_gridspec(2, 2, hspace=0.55, wspace=0.30)
a = fig.add_subplot(gs[0, 0])
b = fig.add_subplot(gs[0, 1])
d = fig.add_subplot(gs[1, :])

for ax in (a, b):
    ax.plot(ideal, ideal, "--", color="gray", lw=1, label="Ideal (linear)")
    ax.set_xscale("log", base=2); ax.set_xticks(ideal); ax.set_xticklabels(ideal)
    ax.set_xlabel("unidades de cálculo")

a.plot(h_x, h_Sf, "o-", color="#2ca02c", label="Híbrido")
a.plot(m_x, m_Sf, "s-", color="#d62728", label="MPI pura")
a.set_title("(a) Escalabilidade forte"); a.set_ylabel("Speed-up")
a.legend(fontsize=7.5, loc="upper left")

b.plot(h_x, h_Sw, "o-", color="#2ca02c", label="Híbrido")
b.plot(m_x, m_Sw, "s-", color="#d62728", label="MPI pura")
b.set_title("(b) Escalabilidade fraca (speed-up)"); b.set_ylabel("Speed-up escalado")
b.legend(fontsize=7.5, loc="upper left")

d.axhline(1.0, color="gray", ls="--", lw=1)
d.plot(h_x, h_Ef, "o-", color="#2ca02c", label="Híbrido")
d.plot(m_x, m_Ef, "s-", color="#d62728", label="MPI pura")
d.set_xscale("log", base=2); d.set_xticks(ideal); d.set_xticklabels(ideal)
d.set_title("(c) Eficiência (forte)"); d.set_xlabel("unidades de cálculo")
d.set_ylabel("Eficiência"); d.set_ylim(0, 1.25)
d.legend(fontsize=7.5, loc="lower left", ncol=2)

fig.savefig(os.path.join(OUT, "graficos.pdf"), bbox_inches="tight")
print("slides/graficos.pdf regenerado (3 paineis, sem coordenador)")
