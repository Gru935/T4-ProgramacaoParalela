#!/bin/bash
# bench.sh - executa os experimentos do Trabalho 4 e gera um CSV de tempos.
#
# Funciona localmente (notebook) e no cluster Atlantica. No cluster, passe um
# hostfile com 1 slot por no para garantir "um processo pesado MPI por no":
#
#     HOSTFILE=hosts.txt ./bench.sh
#
# Variaveis de ambiente (todas opcionais):
#     MAXITER   intensidade de calculo por pixel (default 5000)
#     ROWS      linhas por tarefa MPI (default 64)
#     HOSTFILE  arquivo de hosts do mpirun (sem ele, roda na maquina local)
#     MPIRUN    comando mpirun (default "mpirun")
#     OUT       arquivo csv de saida (default results.csv)
#
# Saida: CSV com colunas versao,np,threads,maxiter,rows,segundos

set -u
MAXITER="${MAXITER:-5000}"
ROWS="${ROWS:-64}"
MPIRUN="${MPIRUN:-mpirun}"
OUT="${OUT:-results.csv}"

HF=""
[ -n "${HOSTFILE:-}" ] && HF="--hostfile ${HOSTFILE}"

# Em notebook (poucos cores) e preciso permitir oversubscribe; no cluster nao.
OVERSUB=""
if [ -z "${HOSTFILE:-}" ]; then OVERSUB="--oversubscribe"; fi

run() {   # run <versao> <np> <threads> <binario> [args...]
  local versao=$1 np=$2 threads=$3 bin=$4; shift 4
  local out secs
  out=$(OMP_NUM_THREADS=$threads $MPIRUN $HF $OVERSUB -np $np "$bin" "$@" 2>/dev/null)
  secs=$(printf '%s\n' "$out" | awk '/Tempo total/{print $3}')
  echo "${versao},${np},${threads},${MAXITER},${ROWS},${secs}"
  echo "${versao},${np},${threads},${MAXITER},${ROWS},${secs}" >> "$OUT"
}

echo "versao,np,threads,maxiter,rows,segundos" > "$OUT"
echo ">> Resultados em $OUT  (MAXITER=$MAXITER ROWS=$ROWS HOSTFILE=${HOSTFILE:-local})"
echo "versao,np,threads,maxiter,rows,segundos"

# ---- baseline sequencial (referencia para speed-up) ----
secs=$(./mandelbrot-seq "$MAXITER" 2>/dev/null | awk '/Tempo total/{print $3}')
echo "seq,1,1,${MAXITER},-,${secs}"
echo "seq,1,1,${MAXITER},-,${secs}" >> "$OUT"

# ---- HIBRIDO: 1 processo MPI por no, variando threads/nos ----
# Ajuste a lista de (np threads) conforme nucleos/no e nos disponiveis.
# Ex.: 2 = 1 coord + 1 worker; 4 = 1 coord + 3 workers (4 nos).
for cfg in "2 1" "2 2" "2 4" "2 8" "3 8" "4 8"; do
  set -- $cfg; run hib "$1" "$2" ./mandelbrot-hib "$MAXITER" "$ROWS"
done

# ---- MPI PURA: 1 processo pesado por core (sem OpenMP) ----
for np in 2 4 8 16; do
  run mpi "$np" 1 ./mandelbrot-mpi "$MAXITER"
done

echo ">> Pronto."
