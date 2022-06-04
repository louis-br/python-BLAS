#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>


#ifndef PROTOCOL_H
#define PROTOCOL_H

#define MAX_BUFFER_SIZE 50816*sizeof(float)

typedef struct
{
    FILE* read;
    FILE* write;
} streams_t;

typedef struct
{
	char command[32];
    char algorithmType;
    float* arrayG;
	int arrayGsize;
} input_message_t;

typedef struct
{
    float* arrayF;
	int arrayFsize;
} output_message_t;

int create_streams(int sock, streams_t *streams);
int read_message(streams_t *streams, input_message_t *message);
int write_message(streams_t *streams, output_message_t *message);


#endif