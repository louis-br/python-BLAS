#include "algorithms.h"

void cgne(float *H, int Hrows, int Hcols, float *f, float *r, float *p) {
    //memcpy(r, g, Hrows*sizeof(float));

    //          Layout,        TransA,       M,     N,     alpha, A, lda,   X, incX, beta, Y, incY
    cblas_sgemv(CblasRowMajor, CblasNoTrans, Hrows, Hcols, -1.0F, H, Hcols, f, 1,    1.0F, r, 1);
    cblas_sgemv(CblasRowMajor, CblasTrans,   Hrows, Hcols, 1.0F,  H, Hcols, r, 1,    0.0F, p, 1);
    for (int i = 0; i < 100; i++) {
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
}