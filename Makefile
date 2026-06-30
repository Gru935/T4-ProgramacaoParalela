# Makefile - Trabalho 4 Programacao Paralela (Mandelbrot)
# Versoes: sequencial (baseline), MPI pura, hibrida MPI+OpenMP
#
# Uso no cluster Atlantica (Linux/gcc):
#     make            # compila as tres versoes
#     make clean
#
# Em macOS (clang + libomp do Homebrew) use:  make OS=mac

CC      = mpicc
CCSEQ   = gcc
CFLAGS  = -O3 -Wall

ifeq ($(OS),mac)
  OMP = -Xpreprocessor -fopenmp -I/opt/homebrew/opt/libomp/include -L/opt/homebrew/opt/libomp/lib -lomp
  CCSEQ = clang
else
  OMP = -fopenmp
endif

all: mandelbrot-seq mandelbrot-mpi mandelbrot-hib

mandelbrot-seq: mandelbrot-seq.c
	$(CCSEQ) $(CFLAGS) $< -o $@ -lm

mandelbrot-mpi: mandelbrot-mpi.c
	$(CC) $(CFLAGS) $< -o $@ -lm

mandelbrot-hib: mandelbrot-hib.c
	$(CC) $(CFLAGS) $< -o $@ $(OMP) -lm

clean:
	rm -f mandelbrot-seq mandelbrot-mpi mandelbrot-hib *.ppm

.PHONY: all clean
