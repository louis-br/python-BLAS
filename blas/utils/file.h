#include <stdio.h>
#include <stdlib.h>

#ifndef FILE_H
#define FILE_H

int import_csv(char *filename, float *array, int arraySize);
int import_bin(char *filename, float *array, int *arraySize);
int export_bin(char *filename, float *array, int arraySize);

#endif