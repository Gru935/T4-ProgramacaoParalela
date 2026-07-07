#include <mpi.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define WIDTH 7680
#define HEIGHT 4320

#define TAG_REQUEST 0
#define TAG_TASK 1
#define TAG_RESULT 2
#define TAG_STOP 3

/* Tamanho padrao do bloco de linhas distribuido pelo coordenador (tarefa MPI).
 * Pode ser sobrescrito pelo segundo argumento da linha de comando. Um bloco
 * suficientemente grande mantem todas as threads OpenMP de um no ocupadas e
 * reduz o overhead de comunicacao MPI; pequeno demais deixa threads ociosas. */
#define DEFAULT_ROWS_PER_TASK 64

/*
 * ==========================================================================
 *  VERSAO HIBRIDA (MPI + OpenMP) do calculo do conjunto de Mandelbrot
 * ==========================================================================
 *
 *  Dois niveis de paralelismo:
 *
 *  1) ENTRE NOS (memoria distribuida, MPI) -- modelo Coordenador/Trabalhador.
 *     Um unico processo pesado MPI por no. O coordenador (rank 0) distribui
 *     blocos de linhas da imagem sob demanda; cada no trabalhador pede uma
 *     tarefa, calcula e devolve o resultado. Identico ao mandelbrot-mpi.c.
 *
 *  2) DENTRO DE CADA NO (memoria compartilhada, OpenMP) -- modelo workpool.
 *     Ao receber um bloco de linhas, o trabalhador processa essas linhas com
 *     varias threads. O controle e feito por uma estrutura de dados
 *     compartilhada (WorkPool): TODAS as threads trabalham e cada uma retira
 *     atomicamente a proxima linha do pool, sem nenhuma thread mestre. Isso
 *     equilibra a carga, que e bastante irregular no Mandelbrot (pontos
 *     dentro do conjunto custam max_iter; fora, terminam cedo).
 */

typedef struct
{
    int start_row;
    int num_rows;
} Task;

/* Estrutura de dados compartilhada que controla o workpool dentro do no.
 * "next" e o indice da proxima linha (relativa ao bloco) ainda nao tomada. */
typedef struct
{
    int next;
    int total;
} WorkPool;

int mandelbrot(double real, double imag, int max_iter)
{
    double z_real = 0.0;
    double z_imag = 0.0;

    int iter = 0;

    while ((z_real * z_real + z_imag * z_imag <= 4.0) &&
           iter < max_iter)
    {
        double temp = z_real * z_real - z_imag * z_imag + real;

        z_imag = 2.0 * z_real * z_imag + imag;
        z_real = temp;

        iter++;
    }

    return iter;
}

void save_ppm(const char *filename, int *image, int max_iter)
{
    FILE *fp = fopen(filename, "w");

    if (fp == NULL)
    {
        printf("Erro ao criar o arquivo %s\n", filename);
        return;
    }

    fprintf(fp, "P3\n");
    fprintf(fp, "%d %d\n", WIDTH, HEIGHT);
    fprintf(fp, "255\n");

    for (int i = 0; i < WIDTH * HEIGHT; i++)
    {
        int color = (image[i] * 255) / max_iter;

        fprintf(fp, "%d %d %d ",
                color,
                color,
                color);

        if ((i + 1) % WIDTH == 0)
            fprintf(fp, "\n");
    }

    fclose(fp);
}

/*
 * Processa um bloco de linhas usando o workpool OpenMP (sem mestre).
 * Todas as threads executam este codigo dentro de uma regiao paralela e
 * disputam, de forma atomica, a proxima linha do pool ate esvazia-lo.
 */
void compute_task_workpool(const Task *task, int *buffer, int max_iter)
{
    WorkPool pool;
    pool.next = 0;
    pool.total = task->num_rows;

    #pragma omp parallel
    {
        while (1)
        {
            int row;

            /* Retira atomicamente a proxima linha do pool compartilhado.
             * Esta e a unica regiao de exclusao mutua: o controle do
             * trabalho esta na estrutura de dados, nao em uma thread mestre. */
            #pragma omp atomic capture
            {
                row = pool.next;
                pool.next++;
            }

            if (row >= pool.total)
                break;

            int y = task->start_row + row;

            for (int x = 0; x < WIDTH; x++)
            {
                double real = -2.5 + (3.5 * x / WIDTH);
                double imag = -1.0 + (2.0 * y / HEIGHT);

                buffer[row * WIDTH + x] = mandelbrot(real, imag, max_iter);
            }
        }
    }
}

int main(int argc, char *argv[])
{
    if (argc < 2)
    {
        printf("Uso: %s <max_iter> [rows_per_task]\n", argv[0]);
        return 1;
    }

    int max_iter = atoi(argv[1]);
    int rows_per_task = (argc >= 3) ? atoi(argv[2]) : DEFAULT_ROWS_PER_TASK;

    if (rows_per_task <= 0)
        rows_per_task = DEFAULT_ROWS_PER_TASK;

    /* MPI com suporte a threads: apenas a thread principal faz chamadas MPI
     * (fora das regioes paralelas), logo MPI_THREAD_FUNNELED e suficiente. */
    int provided;
    MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provided);

    int rank, size;
    double start, end;

    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (size < 2)
    {
        if (rank == 0)
            printf("Execute com pelo menos 2 processos: 1 coordenador e 1 trabalhador.\n");

        MPI_Finalize();
        return 0;
    }

    // =========================
    // COORDENADOR (rank 0)
    // =========================

    if (rank == 0)
    {
        start = MPI_Wtime();

        int *image = malloc(sizeof(int) * WIDTH * HEIGHT);

        if (image == NULL)
        {
            printf("Erro ao alocar memoria para a imagem.\n");
            MPI_Abort(MPI_COMM_WORLD, 1);
        }

        int next_row = 0;
        int rows_completed = 0;
        int workers_stopped = 0;

        MPI_Status status;

        /*
         * A iniciativa e dos trabalhadores:
         * - o trabalhador envia TAG_REQUEST pedindo trabalho;
         * - o coordenador responde com TAG_TASK ou TAG_STOP;
         * - depois o trabalhador envia TAG_RESULT com o resultado.
         */
        while (workers_stopped < size - 1)
        {
            MPI_Probe(MPI_ANY_SOURCE,
                      MPI_ANY_TAG,
                      MPI_COMM_WORLD,
                      &status);

            int worker = status.MPI_SOURCE;

            if (status.MPI_TAG == TAG_REQUEST)
            {
                int request;

                MPI_Recv(&request,
                         1,
                         MPI_INT,
                         worker,
                         TAG_REQUEST,
                         MPI_COMM_WORLD,
                         MPI_STATUS_IGNORE);

                if (next_row < HEIGHT)
                {
                    Task task;

                    task.start_row = next_row;
                    task.num_rows = rows_per_task;

                    if (next_row + rows_per_task > HEIGHT)
                        task.num_rows = HEIGHT - next_row;

                    MPI_Send(&task,
                             sizeof(Task),
                             MPI_BYTE,
                             worker,
                             TAG_TASK,
                             MPI_COMM_WORLD);

                    next_row += task.num_rows;
                }
                else
                {
                    Task stop_task;
                    stop_task.start_row = -1;
                    stop_task.num_rows = 0;

                    MPI_Send(&stop_task,
                             sizeof(Task),
                             MPI_BYTE,
                             worker,
                             TAG_STOP,
                             MPI_COMM_WORLD);

                    workers_stopped++;
                }
            }
            else if (status.MPI_TAG == TAG_RESULT)
            {
                Task result_task;

                MPI_Recv(&result_task,
                         sizeof(Task),
                         MPI_BYTE,
                         worker,
                         TAG_RESULT,
                         MPI_COMM_WORLD,
                         MPI_STATUS_IGNORE);

                int pixels = result_task.num_rows * WIDTH;

                MPI_Recv(&image[result_task.start_row * WIDTH],
                         pixels,
                         MPI_INT,
                         worker,
                         TAG_RESULT,
                         MPI_COMM_WORLD,
                         MPI_STATUS_IGNORE);

                rows_completed += result_task.num_rows;
            }
        }

        end = MPI_Wtime();

        save_ppm("mandelbrot.ppm", image, max_iter);

        free(image);

        printf("Imagem salva em mandelbrot.ppm\n");
        printf("Processos MPI: %d (1 coordenador + %d trabalhadores)\n",
               size, size - 1);
        printf("Threads OpenMP por no: %d\n", omp_get_max_threads());
        printf("Linhas por tarefa: %d\n", rows_per_task);
        printf("Linhas calculadas: %d\n", rows_completed);
        printf("Tempo total: %f segundos\n", end - start);
    }

    // =========================
    // TRABALHADORES (demais ranks)
    // =========================

    else
    {
        MPI_Status status;
        int request = 1;

        while (1)
        {
            // Trabalhador toma a iniciativa e pede trabalho ao coordenador.
            MPI_Send(&request,
                     1,
                     MPI_INT,
                     0,
                     TAG_REQUEST,
                     MPI_COMM_WORLD);

            Task task;

            MPI_Recv(&task,
                     sizeof(Task),
                     MPI_BYTE,
                     0,
                     MPI_ANY_TAG,
                     MPI_COMM_WORLD,
                     &status);

            if (status.MPI_TAG == TAG_STOP)
                break;

            int *buffer = malloc(sizeof(int) * task.num_rows * WIDTH);

            if (buffer == NULL)
            {
                printf("Processo %d: erro ao alocar memoria para o buffer.\n", rank);
                MPI_Abort(MPI_COMM_WORLD, 1);
            }

            // Paralelismo de memoria compartilhada: workpool OpenMP, sem mestre.
            compute_task_workpool(&task, buffer, max_iter);

            MPI_Send(&task,
                     sizeof(Task),
                     MPI_BYTE,
                     0,
                     TAG_RESULT,
                     MPI_COMM_WORLD);

            MPI_Send(buffer,
                     task.num_rows * WIDTH,
                     MPI_INT,
                     0,
                     TAG_RESULT,
                     MPI_COMM_WORLD);

            free(buffer);
        }
    }

    MPI_Finalize();

    return 0;
}
