#include "mkl.h"

#ifndef ALGORITHMS_H
#define ALGORITHMS_H

void cgne(float *H, int Hrows, int Hcols, float *f, float *r);
void cgnr(float *H, int Hrows, int Hcols, float *f, float *r);

#endif