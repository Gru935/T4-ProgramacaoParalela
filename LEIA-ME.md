# Trabalho 4 — Programação Paralela (Mandelbrot híbrido MPI + OpenMP)

Cálculo do conjunto de Mandelbrot (imagem 7680×4320) em três versões:

| Arquivo | Modelo | Uso |
|---|---|---|
| `mandelbrot-seq.c` | Sequencial | Baseline para *speed-up*/eficiência |
| `mandelbrot-mpi.c` | MPI puro, Coordenador/Trabalhador | 1 processo pesado por core |
| `mandelbrot-hib.c` | **Híbrido MPI + OpenMP** | 1 processo pesado por nó + threads |

## Arquitetura da versão híbrida

Dois níveis de paralelismo:

1. **Entre nós (MPI, memória distribuída)** — modelo Coordenador/Trabalhador.
   O `rank 0` distribui blocos de linhas sob demanda; cada nó trabalhador pede
   tarefa, calcula e devolve o resultado. Um único processo pesado MPI por nó.

2. **Dentro do nó (OpenMP, memória compartilhada)** — modelo **workpool sem
   mestre**. Ao receber um bloco de linhas, o trabalhador as processa com
   várias threads. Uma estrutura compartilhada (`WorkPool`) guarda o índice da
   próxima linha; **todas as threads trabalham** e cada uma retira atomicamente
   (`#pragma omp atomic capture`) a próxima linha até esvaziar o pool. Não há
   thread mestre — o controle está na estrutura de dados. Isso equilibra a
   carga, que é muito irregular no Mandelbrot (pontos internos custam
   `max_iter`; externos terminam cedo).

## Compilação

```bash
# No Atlantica (LAD) — wrapper ladcomp; -fopenmp para a versao hibrida:
ladcomp -env mpicc -O3 mandelbrot-mpi.c -o mandelbrot-mpi -lm
ladcomp -env mpicc -O3 mandelbrot-hib.c -o mandelbrot-hib -fopenmp -lm
gcc -O3 mandelbrot-seq.c -o mandelbrot-seq -lm

# No seu notebook:
make            # Linux (gcc + -fopenmp)
make OS=mac     # macOS (clang + libomp do Homebrew)
```

## Execução

Argumentos: `mandelbrot-hib <max_iter> [linhas_por_tarefa]`.
Threads via `OMP_NUM_THREADS` (1 por núcleo, 2 por núcleo com HT).

Cada nó do Atlantica tem **16 CPUs lógicas = 8 núcleos × 2 HT**, logo o híbrido usa
`OMP_NUM_THREADS=16` (**2 threads por núcleo físico** — Hyper-Threading).

```bash
# Atlantica (SLURM) — híbrido SEMPRE em -N 4 -n 5 (4 nós, 1 coordenador + 4
# trabalhadores; o coordenador compartilha o nó 0). A escala é feita variando
# OMP_NUM_THREADS de 1 a 16 (4 a 64 núcleos de cálculo = 4 trab. × threads):
OMP_NUM_THREADS=16 srun --exclusive -N 4 -n 5 --overcommit ./mandelbrot-hib 2000 64

# MPI pura para comparação (1 processo por CPU lógica = 2 por núcleo, HT):
srun --exclusive -N 4 -n 64 ./mandelbrot-mpi 2000

# Local (notebook), com oversubscribe:
OMP_NUM_THREADS=8 mpirun --oversubscribe -np 4 ./mandelbrot-hib 2000 64
```

## Coleta automática dos tempos

`run_atlantica.sh` compila e executa toda a bateria (baseline sequencial,
varredura de threads OpenMP, escalabilidade forte e fraca, alocação do
coordenador e híbrido × MPI pura), gravando `results_t4.csv`:

```bash
./run_atlantica.sh            # MAXITER=2000, base fraca=1500
./run_atlantica.sh 3000 2000  # cargas custom
```

`bench.sh` é o equivalente para rodar **localmente** com `mpirun` (gera o mesmo CSV).

## Acesso ao Atlantica (de fora da PUCRS)

Dois saltos: notebook → `sparta.pucrs.br` (credenciais PUCRS) → `atlantica.lad.pucrs.br` (conta LAD `cp12`).

```bash
# Atencao: o usuario do sparta e portoalegre\<login>  -- SO o login (b.zamin),
# NAO o e-mail completo. Usar o e-mail (...@edu.pucrs.br) e recusado pelo AD.
ssh -l 'portoalegre\b.zamin' sparta.pucrs.br
# já dentro da sparta:
ssh -o PasswordAuthentication=yes cp12@atlantica.lad.pucrs.br
```

## Plano de experimentos (itens de avaliação)

O híbrido roda **sempre em `-N 4 -n 5`** (4 nós, 1 coordenador + 4 trabalhadores)
e a escala é feita **aumentando as threads** (`OMP_NUM_THREADS ∈ {1,2,4,8,16}`,
ou seja `p = 4 × threads` núcleos de cálculo). `S(p)=T(1)/T(p)`, `E(p)=S(p)/p`,
com `T(1)=93,19 s` (sequencial). O `run_atlantica.sh` coleta tudo em `results_t4.csv`.

1. **Escalabilidade forte** — `max_iter=2000` fixo, variando threads. Ideal: `S ∝ p`.

2. **Escalabilidade fraca** — carga por núcleo constante: `max_iter = 1500 × threads`.
   Ideal: tempo constante; `E = T(1 thread)/T(p)`.

3. **Alocação do coordenador** — granularidade de **núcleo** (via `omp_by_rank.sh`).
   Com `-N 4 -n 5` o coordenador (rank 0) e um worker (rank 1) ficam no mesmo nó:
   - *dedica 1 núcleo*: worker do nó 0 usa **15** threads → 1 núcleo livre p/ o
     coordenador (evita oversubscrição) — **melhor**, ~16% mais rápido;
   - *não dedica*: worker do nó 0 usa 16 threads → coordenador compartilha;
   - *dedica um nó* (`-N 4 -n 4`): coordenador sozinho num nó, só 3 trabalhadores
     — **pior** (+63%, desperdiça 1/4 da máquina).

4. **Híbrido × MPI puro** — em 4 nós, híbrido (32/64 threads) vs MPI puro
   (1 processo pesado por core = 32; ou dois por core com HT = 64).
