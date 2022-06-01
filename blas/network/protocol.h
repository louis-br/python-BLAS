#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef PROTOCOL_H
#define PROTOCOL_H

#define MAX_BUFFER_SIZE 50816

int read_message(FILE *stream, char *command, int *algorithmIndex, float *arrayG, int arrayGsize);

#endif