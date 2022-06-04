#include "mkl.h"

#ifndef ALGORITHMS_H
#define ALGORITHMS_H

int cgne(int maxIterations, float minError, float *H, int Hrows, int Hcols, float *f, float *old_r);
int cgnr(int maxIterations, float minError, float *H, int Hrows, int Hcols, float *f, float *r);

#endif