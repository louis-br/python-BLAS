#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mkl.h"

//https://www.intel.com/content/www/us/en/develop/documentation/onemkl-developer-reference-c/top/appendix-d-code-examples/blas-code-examples.html
//MKL_ROOT=/opt/intel/oneapi/mkl/2022.0.2/ gcc mkl.c -o mkl -Wl,--start-group ${MKLROOT}/lib/intel64/libmkl_intel_lp64.a ${MKLROOT}/lib/intel64/libmkl_sequential.a ${MKLROOT}/lib/intel64/libmkl_core.a -Wl,--end-group -lpthread -lm -ldl -m64 -I"${MKLROOT}/include"

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

void cgne(float *H, float *g, float *f, float *r, float *p) {
    /*MKL_INT         m, n, lda, incx, incy;
    MKL_INT         rmaxa, cmaxa;
    float           alpha, beta;
    float          *a, *x, *y;
    CBLAS_LAYOUT    layout;
    CBLAS_TRANSPOSE trans;
    MKL_INT         nx, ny, len_x, len_y;*/
    printf("1\n");
    memcpy(r, g, 50816*sizeof(float));
    printf("2\n");
    //          Layout,        TransA,       M,    N,    alpha,  A, lda,  X, incX, beta, Y, incY
    cblas_sgemv(CblasRowMajor, CblasNoTrans, 50816, 3600, -1.0F, H, 3600, f, 1,    1.0F, r, 1);
    printf("3\n");
    cblas_sgemv(CblasRowMajor, CblasTrans,   50816, 3600, 1.0F,  H, 3600, r, 1,    0.0F, p, 1);
    printf("4\n");
    for (int i = 0; i < 20; i++) {
        //                            N,     X, incX, Y, incY
        float rdot =       cblas_sdot(50816, r, 1,    r, 1);
        printf("5\n");
        float pdot =       cblas_sdot(3600, p, 1,    p, 1);
        float alpha = rdot/pdot;
        printf("6 rdot: %f pdot: %f alpha:%f\n", rdot, pdot, alpha);
        //          N, alpha, X, incX, Y, incY
        cblas_saxpy(3600, alpha, p, 1, f, 1);
        printf("7\n");
        //          Layout,        TransA,       M,    N,    alpha,    A, lda,  X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasNoTrans, 50816, 3600, -alpha,  H, 3600, p, 1,    1.0F, r, 1);
        printf("8\n");
        //                      N,     X, incX, Y, incY
        float beta = cblas_sdot(50816, r, 1,    r, 1)/rdot;
        printf("9 beta: %f\n", beta);
        //          Layout,        TransA,     M,     N,    alpha, A, lda,  X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasTrans, 50816, 3600, 1.0F,  H, 3600, r, 1,    beta, p, 1);
        printf("10\n");
    }
}

int main()
{
    MKL_INT         m, n, lda, incx, incy, i, j;
    MKL_INT         rmaxa, cmaxa;
    float           alpha;
    float          *a, *x, *y;
    CBLAS_LAYOUT    layout;
    MKL_INT         len_x, len_y;

    m = 2;
    n = 3;
    lda = 5;
    incx = 2;
    incy = 1;
    alpha = 0.5;
                    layout = CblasRowMajor;

    len_x = 10;
    len_y = 10;
    rmaxa = m + 1;
    cmaxa = n;
    a = (float *)calloc( rmaxa*cmaxa, sizeof(float) );
    x = (float *)calloc( len_x, sizeof(float) );
    y = (float *)calloc( len_y, sizeof(float) );
    if( a == NULL || x == NULL || y == NULL ) {
        printf( "\n Can't allocate memory for arrays\n");
        return 1;
    }
    if( layout == CblasRowMajor )
        lda=cmaxa;
    else
        lda=rmaxa;

    for (i = 0; i < 10; i++) {
        x[i] = 1.0;
        y[i] = 1.0;
    }
    
    for (i = 0; i < m; i++) {
        for (j = 0; j < n; j++) {
            a[i + j*lda] = j + 1;
        }
    }

    cblas_sger(layout, m, n, alpha, x, incx, y, incy, a, lda);

    printf("%f", a[0]);
    //PrintArrayS(&layout, FULLPRINT, GENERAL_MATRIX, &m, &n, a, &lda, "A");

    free(a);
    free(x);
    free(y);

    float *H = (float *)calloc(50816*3600, sizeof(float));
    float *g = (float *)calloc(50816, sizeof(float));
    float *f = (float *)calloc(3600, sizeof(float));
    float *r = (float *)calloc(50816, sizeof(float));
    float *p = (float *)calloc(3600, sizeof(float));

    read_csv("../../data/G-1.csv", g, 50816);
    printf("Done reading csv: g\n");
    
    read_csv("../../data/H-1.csv", H, 50816*3600);
    printf("Done reading csv: H\n");
    //printf("%e", H[(50300-1)*3600]);
    cgne(H, g, f, r, p);

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
    free(p);
    
    return 0;
}