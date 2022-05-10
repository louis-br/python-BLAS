#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <linux/in.h>
#include <unistd.h>

#include "mkl.h"

typedef struct
{
	int sock;
	struct sockaddr address;
	int addr_len;
} connection_t;

float* H;

int read_csv(char *filename, float *array, int length) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        printf("Cannot open file: %s\n", filename);
        return 0;
    }

    /*FILE *file;

    fseek(disk, 0, SEEK_END);
    long size = ftell(disk);
    rewind(disk);
    char *buffer = (char *)malloc(size*sizeof(char));
    if (buffer != NULL) {
        if (fread(buffer, sizeof(char), size, disk) != size) {
            printf("Error copying to memory\n");
            return 0;
        }
        file = fmemopen(buffer, size*sizeof(char), "r");
        fclose(disk);
    } else {
        printf("Not enough memory for the whole file\n");
        file = disk;
    }

    printf("Size: %ld\n", size);*/

    float f;
    int i = 0;
    int c = 0;
    while (c >= 0) {
        c = fscanf(file, "%f%*[,;\n\r]", &f);
        if (c == EOF) {
            return 0;
        }
        if (c == 0) {
            printf("Failed to load float after: %e, read: %i bytes\n", f, c);
            return 0; 
        }
        array[i] = f;
        i += c;
        if (i > length) {
            printf("Array too small\n");
            return 0;
        }
    }

    return fclose(file) + 1;
}

void cgne(float *H, float *f, float *r, float *p) {
    /*MKL_INT         m, n, lda, incx, incy;
    MKL_INT         rmaxa, cmaxa;
    float           alpha, beta;
    float          *a, *x, *y;
    CBLAS_LAYOUT    layout;
    CBLAS_TRANSPOSE trans;
    MKL_INT         nx, ny, len_x, len_y;*/
    //printf("1\n");
    //memcpy(r, g, 50816*sizeof(float));
    //printf("2\n");
    //          Layout,        TransA,       M,    N,    alpha,  A, lda,  X, incX, beta, Y, incY
    cblas_sgemv(CblasRowMajor, CblasNoTrans, 50816, 3600, -1.0F, H, 3600, f, 1,    1.0F, r, 1);
    //printf("3\n");
    cblas_sgemv(CblasRowMajor, CblasTrans,   50816, 3600, 1.0F,  H, 3600, r, 1,    0.0F, p, 1);
    //printf("4\n");
    for (int i = 0; i < 100; i++) {
        //                            N,     X, incX, Y, incY
        float rdot =       cblas_sdot(50816, r, 1,    r, 1);
        //printf("5\n");
        float pdot =       cblas_sdot(3600, p, 1,    p, 1);
        float alpha = rdot/pdot;
        //printf("6 rdot: %f pdot: %f alpha:%f\n", rdot, pdot, alpha);
        //          N, alpha, X, incX, Y, incY
        cblas_saxpy(3600, alpha, p, 1, f, 1);
        //printf("7\n");
        //          Layout,        TransA,       M,    N,    alpha,    A, lda,  X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasNoTrans, 50816, 3600, -alpha,  H, 3600, p, 1,    1.0F, r, 1);
        //printf("8\n");
        //                      N,     X, incX, Y, incY
        float beta = cblas_sdot(50816, r, 1,    r, 1)/rdot;
        //printf("9 beta: %f\n", beta);
        //          Layout,        TransA,     M,     N,    alpha, A, lda,  X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasTrans, 50816, 3600, 1.0F,  H, 3600, r, 1,    beta, p, 1);
        //printf("10\n");
    }
}

void *process(void* ptr) {
    if (ptr == NULL) {
        pthread_exit(0);
    }

    connection_t* connection = (connection_t *)ptr;

    int size = 1;
    //read(connection->sock, &size, sizeof(int));
    printf("got size: %i\n", size);
    if (size > 0) {
        float *r = (float *)calloc(50816, sizeof(float));
        float *f = (float *)calloc(3600, sizeof(float));
        float *p = (float *)calloc(3600, sizeof(float));

        int size = 50816*sizeof(float);
        int offset = 0;

        while (offset < size) {
            printf("offset: %d\n", offset);
            offset += read(connection->sock, ((void *)r + offset), size - offset);
        }

        printf("r[10000]: %e r[10001]: %e\n", r[10000], r[10001]);

        printf("CGNE begin\n");
        cgne(H, f, r, p);
        printf("CGNE end\n");

        //printf("f[0] = %f\n", f[0]);

        printf("wrote %i\n", write(connection->sock, f, 3600*sizeof(float)));

        /*for (int i=0; i < 3600; i++) {
            printf("%e", f[i]);
            //printf("1");
            if ((i + 1) % 60 == 0) {
                printf("\n");
            } else if (i != (3600 - 1)) {
                printf(",");
            }
        }*/

        free(f);
        free(r);
        free(p);
    }

    close(connection->sock);
    free(connection);
    pthread_exit(0);
}

int main()
{
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock < 0) {
        printf("Failed to create socket\n");
        return -1;
    }

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(3333);
    if (bind(sock, (struct sockaddr *)&address, sizeof(struct sockaddr_in)) < 0) {
        printf("Failed to bind socket\n");
        return -2;
    }

    if (listen(sock, 60) < 0) {
        printf("Failed to listen\n");
        return -3;
    }

    H = (float *)calloc(50816*3600, sizeof(float));

    read_csv("../data/H-1.csv", H, 50816*3600);
    printf("Done reading csv: H\n");

    while (1) {
        connection_t *connection = (connection_t*)malloc(sizeof(connection_t));
        connection->sock = accept(sock, &connection->address, &connection->addr_len);
        printf("got connection\n");
        if (connection->sock <= 0) {
            free(connection);
        } else {
	        pthread_t thread;
            pthread_create(&thread, 0, process, (void *)connection);
            pthread_detach(thread);
        }
    }


    /*
    read_csv("../data/G-1.csv", g, 50816);
    printf("Done reading csv: g\n");
    
    read_csv("../data/H-1.csv", H, 50816*3600);
    printf("Done reading csv: H\n");


    for (int i=0; i < 3600; i++) {
        printf("%e", f[i]);
        //printf("1");
        if ((i + 1) % 60 == 0) {
            printf("\n");
        } else if (i != (3600 - 1)) {
            printf(",");
        }
    }

    free(H);
    free(g);
    free(f);
    free(r);
    free(p);*/
    
    return 0;
}