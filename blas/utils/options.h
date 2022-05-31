#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>

#ifndef OPTIONS_h
#define OPTIONS_h

#define ADDRESS_SIZE 46

typedef struct
{
	char address[ADDRESS_SIZE];
	int port;
} options_t;

int set_options(int argc, char **argv, options_t *options);

#endif