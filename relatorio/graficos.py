#!/usr/bin/env python3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEQ = 93.194233

# --- dados (results_t4.csv) ---
th       = [1, 2, 4, 8, 16]
t_omp    = [87.006309, 43.679385, 23.400256, 11.850233, 6.849682]
S_omp    = [t_omp[0]/x for x in t_omp]

nodes    = [2, 3, 4]
# Para o ponto de 4 nós usa-se a medicao do experimento do coordenador
# (2.962407 s, pareada com o caso "compartilhado"), igual a Tabela 4.
t_hib    = [7.075377, 3.454101, 2.962407]
t_mpiht  = [3.351889, 2.735431, 2.002144]
S_hib    = [SEQ/x for x in t_hib]
S_mpiht  = [SEQ/x for x in t_mpiht]

coord_lbl = ["Dedicado\n(3 workers)", "Compartilhado\n(4 workers)"]
coord_t   = [2.962407, 2.349887]

t_fraca  = [5.248208, 5.058961, 5.404228]   # carga ∝ workers (1500/3000/4500)

plt.rcParams.update({"font.size": 8.5, "axes.grid": True,
                     "grid.alpha": 0.35, "axes.axisbelow": True})
fig, ax = plt.subplots(2, 2, figsize=(8.0, 4.35))

# (a) Workpool OpenMP — speedup x threads
a = ax[0,0]
a.plot(th, th, "--", color="gray", label="Ideal")
a.plot(th, S_omp, "o-", color="#1f77b4", label="Workpool")
a.axvline(8, color="orange", ls=":", lw=1); a.text(8.2, 1.5, "8 núcleos\nfísicos", fontsize=7, color="orange")
a.set_title("(a) Workpool OpenMP (1 nó trabalhador)")
a.set_xlabel("threads"); a.set_ylabel("Speed-up (vs 1 thread)")
a.set_xticks(th); a.legend(fontsize=8, loc="upper left")

# (b) Escalabilidade forte — speedup x nós: híbrido vs MPI pura
b = ax[0,1]
b.plot(nodes, S_hib,   "o-", color="#2ca02c", label="Híbrido (1 proc/nó+16 th)")
b.plot(nodes, S_mpiht, "s-", color="#d62728", label="MPI pura (16 proc/nó, HT)")
for x,y in zip(nodes,S_hib):   b.annotate(f"{y:.0f}×", (x,y), textcoords="offset points", xytext=(0,-12), fontsize=7)
for x,y in zip(nodes,S_mpiht): b.annotate(f"{y:.0f}×", (x,y), textcoords="offset points", xytext=(0,6), fontsize=7)
b.set_title("(b) Escalabilidade forte (max_iter=2000)")
b.set_xlabel("nós"); b.set_ylabel("Speed-up (vs sequencial)")
b.set_xticks(nodes); b.legend(fontsize=7.5, loc="upper left")

# (c) Alocação do coordenador — barras
c = ax[1,0]
bars = c.bar(coord_lbl, coord_t, color=["#9467bd", "#17becf"], width=0.55)
for r,v in zip(bars, coord_t): c.text(r.get_x()+r.get_width()/2, v+0.05, f"{v:.2f}s", ha="center", fontsize=8)
c.set_title("(c) Alocação do coordenador (4 nós)")
c.set_ylabel("Tempo (s)"); c.set_ylim(0, 3.6)
c.annotate("−20,7%", xy=(1, 2.35), xytext=(1, 3.15), ha="center", color="green",
           fontsize=9, fontweight="bold",
           arrowprops=dict(arrowstyle="->", color="green", lw=1.3))

# (d) Escalabilidade fraca — tempo ~constante
d = ax[1,1]
d.plot(nodes, t_fraca, "D-", color="#8c564b", label="Híbrido (carga ∝ workers)")
d.axhline(t_fraca[0], color="gray", ls="--", lw=1, label="Ideal (constante)")
for x,y in zip(nodes,t_fraca): d.annotate(f"{y:.2f}s", (x,y), textcoords="offset points", xytext=(0,7), fontsize=7)
d.set_title("(d) Escalabilidade fraca")
d.set_xlabel("nós  (max_iter = 1500×workers)"); d.set_ylabel("Tempo (s)")
d.set_xticks(nodes); d.set_ylim(0, 6.5); d.legend(fontsize=7.5, loc="lower left")

fig.tight_layout(pad=0.5)
out = "/Users/bernardozamin/Documents/Ultimo semestre/T4-ProgramacaoParalela/relatorio/graficos.pdf"
import os; os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out)
print("salvo:", out)
