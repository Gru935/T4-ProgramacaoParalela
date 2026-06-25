#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define WIDTH 7680
#define HEIGHT 4320

/*
 * Versao sequencial (sem MPI) usada como referencia (baseline) para o
 * calculo de speed-up e eficiencia. Faz exatamente o mesmo calculo da
 * versao paralela (mesmo mapeamento de coordenadas e mesmo algoritmo),
 * porem em um unico processo, percorrendo todas as linhas da imagem.
 */

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
        printf("Uso: %s <max_iter>\n", argv[0]);
        return 1;
    }

    int max_iter = atoi(argv[1]);

    int *image = malloc(sizeof(int) * WIDTH * HEIGHT);

    if (image == NULL)
    {
        printf("Erro ao alocar memoria para a imagem.\n");
        return 1;
    }

    struct timespec t_start, t_end;
    clock_gettime(CLOCK_MONOTONIC, &t_start);

    // Percorre todas as linhas da imagem em um unico processo.
    for (int y = 0; y < HEIGHT; y++)
    {
        for (int x = 0; x < WIDTH; x++)
        {
            double real = -2.5 + (3.5 * x / WIDTH);
            double imag = -1.0 + (2.0 * y / HEIGHT);

            image[y * WIDTH + x] = mandelbrot(real, imag, max_iter);
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &t_end);

    double elapsed = (t_end.tv_sec - t_start.tv_sec) +
                     (t_end.tv_nsec - t_start.tv_nsec) / 1e9;

    save_ppm("mandelbrot.ppm", image, max_iter);

    free(image);

    printf("Imagem salva em mandelbrot.ppm\n");
    printf("Tempo total: %f segundos\n", elapsed);

    return 0;
}
