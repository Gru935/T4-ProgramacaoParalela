#!/bin/bash
# Define OMP_NUM_THREADS por rank MPI. O rank 1 (worker co-localizado com o
# coordenador no no 0) usa 15 threads, DEIXANDO 1 nucleo dedicado ao
# coordenador (rank 0); os demais workers usam 16 threads.
if [ "$SLURM_PROCID" -eq 1 ]; then
  export OMP_NUM_THREADS=15
else
  export OMP_NUM_THREADS=16
fi
exec ./mandelbrot-hib "$@"
