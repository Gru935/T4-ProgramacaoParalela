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
`OMP_NUM_THREADS=16` (uma thread por núcleo lógico).

```bash
# Atlantica (SLURM) — 1 processo pesado MPI por nó, em 4 nós:
#   --exclusive -N 4 -n 4  -> 1 tarefa por nó (1 coordenador + 3 trabalhadores)
#   -c 16                  -> as 16 CPUs do nó ficam disponíveis para as threads
OMP_NUM_THREADS=16 srun --exclusive -N 4 -n 4 -c 16 ./mandelbrot-hib 2000 64

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

O script `bench.sh` gera um `results.csv` (`versao,np,threads,maxiter,rows,segundos`).
Ajuste a lista de configurações conforme nº de núcleos/nó da Atlantica.

1. **Speed-up e eficiência (4 nós).** `S(p)=T_seq/T(p)`, `E(p)=S(p)/p`,
   onde `p` = nº de núcleos efetivamente computando.

2. **Escalabilidade forte** — problema fixo (`max_iter` e imagem constantes),
   aumentar recursos (threads e nós). Ideal: tempo cai ∝ `p`.

3. **Escalabilidade fraca** — carga por recurso constante: `max_iter ∝ p`.
   Ideal: tempo aproximadamente constante; `E = T(1)/T(p)`.

4. **Alocação do coordenador** — comparar:
   - *dedicado*: 4 processos em 4 nós → 1 coordenador + 3 trabalhadores (o nó do
     coordenador fica ocioso, pois ele só distribui tarefas);
   - *não dedicado*: 5 processos em 4 nós → coordenador divide o nó 0 com um
     trabalhador (4 nós computando). Controlado pelo hostfile, sem mudar o código.

5. **Híbrido × MPI puro** — nas 4 máquinas, comparar o híbrido (1 processo/nó +
   threads) com o MPI puro (1 processo pesado por core, ou 2 por core com HT).
