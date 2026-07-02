#!/usr/bin/env python3
# Duas figuras (uma por slide): forte (speed-up + eficiencia) e fraca idem.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

OUT = os.path.dirname(os.path.abspath(__file__))
SEQ_H = 93.194233

h_x  = [4, 8, 16, 32, 64]
h_Sf = [SEQ_H/t for t in [21.888989, 10.976950, 5.855055, 3.314190, 2.012548]]
h_Ef = [s/c for s, c in zip(h_Sf, h_x)]
h_carga = [1500, 3000, 6000, 12000, 24000]
h_texec = [16.594238, 16.339467, 16.879343, 17.745419, 22.178566]
h_Sw = [(SEQ_H*c/2000.0)/tw for c, tw in zip(h_carga, h_texec)]
h_Ew = [s/c for s, c in zip(h_Sw, h_x)]

m_x  = [1, 4, 8, 16, 32, 64]
m_Sf = [1, 2.97486, 6.91680, 14.33712, 28.07063, 44.11489]
m_Ef = [1, 0.743716, 0.864600, 0.896070, 0.877207, 0.689295]
m_Sw = [1, 3.07502, 7.22688, 15.45444, 30.34855, 48.47850]
m_Ew = [1, 0.768756, 0.903360, 0.965902, 0.948392, 0.757477]

plt.rcParams.update({"font.size": 11, "axes.grid": True, "grid.alpha": 0.35,
                     "axes.axisbelow": True})
ideal = [1, 4, 8, 16, 32, 64]

def xaxis(ax):
    ax.set_xscale("log", base=2); ax.set_xticks(ideal); ax.set_xticklabels(ideal)
    ax.set_xlabel("nº de processadores")

def make(fname, S_title, h_S, m_S, E_h, E_m, ylab_s):
    fig, (s, e) = plt.subplots(1, 2, figsize=(9.6, 2.8))
    fig.subplots_adjust(wspace=0.28, bottom=0.22, top=0.88)
    # speed-up
    xaxis(s)
    s.plot(ideal, ideal, "--", color="gray", lw=1.5, label="Ideal (linear)")
    s.plot(h_x, h_S, "o-", color="#2ca02c", lw=2.2, ms=7, label="Híbrido")
    s.plot(m_x, m_S, "s-", color="#d62728", lw=2.2, ms=6, label="MPI pura")
    s.set_title(S_title); s.set_ylabel(ylab_s)
    s.legend(fontsize=9, loc="upper left")
    # eficiencia
    xaxis(e)
    e.axhline(1.0, color="gray", ls="--", lw=1.5)
    e.plot(h_x, E_h, "o-", color="#2ca02c", lw=2.2, ms=7, label="Híbrido")
    e.plot(m_x, E_m, "s-", color="#d62728", lw=2.2, ms=6, label="MPI pura")
    e.set_title("Eficiência"); e.set_ylabel("Eficiência"); e.set_ylim(0, 1.25)
    e.legend(fontsize=9, loc="lower left")
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight"); plt.close(fig)

make("graficos_forte.pdf", "Speed-up (forte)", h_Sf, m_Sf, h_Ef, m_Ef, "Speed-up")
make("graficos_fraca.pdf", "Speed-up (fraca)", h_Sw, m_Sw, h_Ew, m_Ew, "Speed-up escalado")
print("graficos_forte.pdf e graficos_fraca.pdf gerados")
