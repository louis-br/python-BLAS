#include <stdio.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <linux/in.h>
#include <unistd.h>

#ifndef SERVER_H
#define SERVER_H

typedef struct
{
	int sock;
	struct sockaddr address;
	int addr_len;
} connection_t;

int create_server();

#endif