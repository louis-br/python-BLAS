#include "algorithms.h"

void cgne(float *H, int Hrows, int Hcols, float *f, float *r) {
    float *p = (float *)calloc(Hcols, sizeof(float));

    //          Layout,        TransA,       M,     N,     alpha, A, lda,   X, incX, beta, Y, incY
    cblas_sgemv(CblasRowMajor, CblasNoTrans, Hrows, Hcols, -1.0F, H, Hcols, f, 1,    1.0F, r, 1);
    cblas_sgemv(CblasRowMajor, CblasTrans,   Hrows, Hcols, 1.0F,  H, Hcols, r, 1,    0.0F, p, 1);
    for (int i = 0; i < 10; i++) {
        //                            N,     X, incX, Y, incY
        float rdot =       cblas_sdot(Hrows, r, 1,    r, 1);
        float alpha = rdot/cblas_sdot(Hcols, p, 1,    p, 1);
        //          N,     alpha, X, incX, Y, incY
        cblas_saxpy(Hcols, alpha, p, 1,    f, 1);
        //          Layout,        TransA,       M,     N,     alpha,   A, lda,   X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasNoTrans, Hrows, Hcols, -alpha,  H, Hcols, p, 1,    1.0F, r, 1);
        //                      N,     X, incX, Y, incY
        float beta = cblas_sdot(Hrows, r, 1,    r, 1)/rdot;
        //          Layout,        TransA,     M,     N,     alpha, A, lda,   X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasTrans, Hrows, Hcols, 1.0F,  H, Hcols, r, 1,    beta, p, 1);
    }

    free(p);
}

void cgnr(float *H, int Hrows, int Hcols, float *f, float *r) {
    float *p = (float *)calloc(Hcols, sizeof(float));
    float *z = (float *)calloc(Hcols, sizeof(float));
    float *w = (float *)calloc(Hrows, sizeof(float));

    //          Layout,        TransA,       M,     N,     alpha, A, lda,   X, incX, beta, Y, incY
    cblas_sgemv(CblasRowMajor, CblasNoTrans, Hrows, Hcols, -1.0F, H, Hcols, f, 1,    1.0F, r, 1);
    cblas_sgemv(CblasRowMajor, CblasTrans,   Hrows, Hcols, 1.0F,  H, Hcols, r, 1,    0.0F, z, 1);
    //          N      X, incX, Y, incY
    cblas_scopy(Hcols, z, 1,    p, 1);
    for (int i = 0; i < 10; i++) {
        //          Layout,        TransA,       M,     N,     alpha, A, lda,   X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasNoTrans, Hrows, Hcols, 1.0F,  H, Hcols, p, 1,    0.0F, w, 1);

        //                         N,     X, incX
        float znorm2 = cblas_snrm2(Hcols, z, 1);
        float wnorm2 = cblas_snrm2(Hrows, w, 1);

        float alpha = (znorm2*znorm2)/(wnorm2*wnorm2);

        //          N,     alpha,  X, incX, Y, incY
        cblas_saxpy(Hcols, alpha,  p, 1,    f, 1);
        cblas_saxpy(Hrows, -alpha, w, 1,    r, 1);

        //          Layout,        TransA,     M,     N,     alpha, A, lda,   X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasTrans, Hrows, Hcols, 1.0F,  H, Hcols, r, 1,    0.0F, z, 1);

        //                          N,     X, incX
        float z1norm2 = cblas_snrm2(Hcols, z, 1);

        float beta = (z1norm2*z1norm2)/(znorm2*znorm2);

        //          N,     alpha, X, incX
        cblas_sscal(Hcols, beta,  p, 1);
        //          N,     alpha,  X, incX, Y, incY
        cblas_saxpy(Hcols, 1.0F,  z,  1,    p, 1);
    }

    free(p);
    free(z);
    free(w);
}