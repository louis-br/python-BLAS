#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef NETWORK_H
#define NETWORK_H

int read_message(FILE *stream, char *command, int *algorithmIndex, float *arrayG);

#endif