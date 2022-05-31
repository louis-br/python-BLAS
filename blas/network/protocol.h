#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef PROTOCOL_H
#define PROTOCOL_H

int read_message(FILE *stream, char *command, int *algorithmIndex, float *arrayG);

#endif