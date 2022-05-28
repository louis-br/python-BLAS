#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <linux/in.h>
#include <unistd.h>

#include "omp.h"

#include "algorithms.h"
#include "network.h"
#include "file.h"

typedef struct
{
	int sock;
	struct sockaddr address;
	int addr_len;
} connection_t;

float* H;

void process(connection_t *connection) {
    FILE *readStream = NULL;
    FILE *writeStream = NULL;
    {
        int writeSock = dup(connection->sock);
        if (writeSock < 0) { printf("Failed to duplicate socket\n"); return; }
        writeStream = fdopen(writeSock, "w");
    }
    readStream = fdopen(connection->sock, "r");
    setvbuf(readStream, NULL, _IONBF, 0);

    if (readStream == NULL || writeStream == NULL) { printf("Failed to create stream\n"); return; }

    char command[32] = "";
    int algorithmIndex = 0;
    float *r = (float *)calloc(50816, sizeof(float));
    
    read_message(readStream, command, &algorithmIndex, r);
    printf("Command: %s algorithmIndex: %i\n", command, algorithmIndex);
    
    float *f = (float *)calloc(3600, sizeof(float));
    float *p = (float *)calloc(3600, sizeof(float));

    /*int size = 50816*sizeof(float);
    int offset = 0;

    while (offset < size) {
        printf("offset: %d\n", offset);
        offset += read(connection->sock, ((void *)r + offset), size - offset);
    }*/

    printf("r[10000]: %e r[10001]: %e\n", r[10000], r[10001]);

    printf("CGNE begin\n");
    cgne(H, 50816, 3600, f, r, p); //H, f, r, p);
    printf("CGNE end\n");

    printf("wrote %i\n", write(connection->sock, f, 3600*sizeof(float)));

    free(f);
    free(r);
    free(p);

    fclose(writeStream);
    fclose(readStream);

    close(connection->sock);
    free(connection);
}

int main()
{
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock < 0) {
        printf("Failed to create socket\n");
        return -1;
    }

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(3333);
    if (bind(sock, (struct sockaddr *)&address, sizeof(struct sockaddr_in)) < 0) {
        printf("Failed to bind socket\n");
        return -2;
    }

    if (listen(sock, 60) < 0) {
        printf("Failed to listen\n");
        return -3;
    }

    H = (float *)calloc(50816*3600, sizeof(float));

    read_csv("../data/H-1.csv", H, 50816*3600);
    printf("Done reading csv: H\n");

    #pragma omp parallel default(none) shared(sock) shared(H)
    {
        #pragma omp single nowait
        while (1) {
            connection_t *connection = (connection_t*)malloc(sizeof(connection_t));
            connection->sock = accept(sock, &connection->address, &connection->addr_len);
            printf("got connection\n");
            if (connection->sock <= 0) {
                free(connection);
            } else {//single nowait
                #pragma omp task untied
                {
                    process(connection);
                }
                //pthread_t thread;
                //pthread_create(&thread, 0, process, (void *)connection);
                //pthread_detach(thread);
            }
        }
    }

    free(H);
    
    return 0;
}