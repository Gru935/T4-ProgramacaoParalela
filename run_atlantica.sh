#!/bin/bash
# =============================================================================
#  run_atlantica.sh - coleta de tempos do Trabalho 4 (Mandelbrot hibrido)
#  no cluster Atlantica (SLURM). Gera results_t4.csv para montar as tabelas
#  e graficos de speed-up / eficiencia do relatorio.
#
#  Uso (dentro do diretorio do repo, no atlantica):
#     ./run_atlantica.sh                 # MAXITER=2000, base fraca=1500
#     ./run_atlantica.sh 3000 2000       # MAXITER e base custom
#
#  Nos do Atlantica: 16 CPUs logicas = 8 nucleos x 2 HT. Por isso o hibrido
#  usa OMP_NUM_THREADS=16 (duas threads por nucleo) e a MPI pura usa ate
#  16 processos por no.
#
#  CSV: experimento,versao,nodes,procs,threads,maxiter,rows,segundos
# =============================================================================
set -u
cd "$(dirname "$0")" || exit 1

# mpicc do LAD (para o ladcomp funcionar fora de um shell de login)
export PATH=/LADAPPs/OpenMPI/openmpi-4.1.1/bin:$PATH

# Trava: garante uma unica execucao simultanea deste driver.
exec 9>.run_atlantica.lock
flock -n 9 || { echo "Ja existe uma execucao em andamento; saindo."; exit 0; }

MAXITER=${1:-2000}      # carga fixa para escalabilidade FORTE
WEAK_BASE=${2:-1500}    # carga por trabalhador para escalabilidade FRACA
ROWS=64
OUT=results_t4.csv
LADCOMP=/LADAPPs/ladscripts/ladcomp

# Descarta a escrita do PPM (232 MB): nao afeta o tempo medido, que e tomado
# ANTES do save_ppm. Acelera muito a varredura e poupa I/O no NFS.
ln -sf /dev/null mandelbrot.ppm

echo "### Compilando com ladcomp (-O3) ..."
gcc -O3 mandelbrot-seq.c -o mandelbrot-seq -lm                          || exit 1
$LADCOMP -env mpicc -O3 mandelbrot-mpi.c -o mandelbrot-mpi -lm          || exit 1
$LADCOMP -env mpicc -O3 mandelbrot-hib.c -o mandelbrot-hib -fopenmp -lm || exit 1
echo "### OK. MAXITER=$MAXITER WEAK_BASE=$WEAK_BASE"

gt(){ awk '/Tempo total/{print $3}'; }
echo "experimento,versao,nodes,procs,threads,maxiter,rows,segundos" > $OUT
emit(){ echo "RESULT $*"; echo "$*" >> $OUT; }

# ---------- baseline sequencial (referencia do speed-up) ----------
t=$(./mandelbrot-seq $MAXITER | gt);                 emit "baseline,seq,1,1,1,$MAXITER,-,$t"

# ---------- workpool OpenMP: threads dentro de UM trabalhador (N=2) ----------
for th in 1 2 4 8 16; do
  t=$(OMP_NUM_THREADS=$th srun --exclusive -N 2 -n 2 -c 16 ./mandelbrot-hib $MAXITER $ROWS | gt)
  emit "omp_threads,hib,2,2,$th,$MAXITER,$ROWS,$t"
done

# ---------- escalabilidade FORTE: HIBRIDO, 16 threads/no, varia nos ----------
for N in 2 3 4; do
  t=$(OMP_NUM_THREADS=16 srun --exclusive -N $N -n $N -c 16 ./mandelbrot-hib $MAXITER $ROWS | gt)
  emit "forte_hib,hib,$N,$N,16,$MAXITER,$ROWS,$t"
done

# ---------- escalabilidade FORTE: MPI PURA, 1 processo por CPU logica (HT) ----
for N in 2 3 4; do
  np=$((N*16))
  t=$(srun --exclusive -N $N -n $np ./mandelbrot-mpi $MAXITER | gt)
  emit "forte_mpi_ht,mpi,$N,$np,1,$MAXITER,-,$t"
done

# ---------- escalabilidade FORTE: MPI PURA, 1 processo por nucleo fisico ------
for N in 2 3 4; do
  np=$((N*8))
  t=$(srun --exclusive -N $N -n $np ./mandelbrot-mpi $MAXITER | gt)
  emit "forte_mpi_core,mpi,$N,$np,1,$MAXITER,-,$t"
done

# ---------- alocacao do COORDENADOR (4 nos) ----------
# dedicado: 1 coord + 3 workers (no do coordenador fica ocioso)
t=$(OMP_NUM_THREADS=16 srun --exclusive -N 4 -n 4 -c 16 ./mandelbrot-hib $MAXITER $ROWS | gt)
emit "coord_dedicado,hib,4,4,16,$MAXITER,$ROWS,$t"
# nao dedicado: 1 coord + 4 workers (coordenador divide o no 0 com um worker)
t=$(OMP_NUM_THREADS=16 srun --exclusive -N 4 -n 5 --overcommit ./mandelbrot-hib $MAXITER $ROWS | gt)
emit "coord_compartilhado,hib,4,5,16,$MAXITER,$ROWS,$t"

# ---------- escalabilidade FRACA: HIBRIDO, carga proporcional aos workers -----
for N in 2 3 4; do
  w=$((N-1)); mi=$((WEAK_BASE*w))
  t=$(OMP_NUM_THREADS=16 srun --exclusive -N $N -n $N -c 16 ./mandelbrot-hib $mi $ROWS | gt)
  emit "fraca_hib,hib,$N,$N,16,$mi,$ROWS,$t"
done

echo "### FIM - resultados em $OUT"
echo "ALL_DONE"
