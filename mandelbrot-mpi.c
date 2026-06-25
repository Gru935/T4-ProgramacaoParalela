#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define WIDTH 7680
#define HEIGHT 4320

#define TAG_REQUEST 0
#define TAG_TASK 1
#define TAG_RESULT 2
#define TAG_STOP 3

typedef struct
{
    int start_row;
    int num_rows;
} Task;

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

int main(int argc, char *argv[])
{
    if (argc != 2)
    {
        return 1;
    }

    int max_iter = atoi(argv[1]);

    MPI_Init(&argc, &argv);

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
    // COORDENADOR
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
        int rows_per_task = 10;
        int workers_stopped = 0;

        MPI_Status status;

        /*
         * Agora a iniciativa e dos trabalhadores:
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
        printf("Linhas calculadas: %d\n", rows_completed);
        printf("Tempo total: %f segundos\n", end - start);
    }

    // =========================
    // WORKERS
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

            for (int row = 0; row < task.num_rows; row++)
            {
                int y = task.start_row + row;

                for (int x = 0; x < WIDTH; x++)
                {
                    double real = -2.5 + (3.5 * x / WIDTH);
                    double imag = -1.0 + (2.0 * y / HEIGHT);

                    int iter = mandelbrot(real, imag, max_iter);

                    buffer[row * WIDTH + x] = iter;
                }
            }

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
