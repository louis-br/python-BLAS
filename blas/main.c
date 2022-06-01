#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <linux/in.h>
#include <unistd.h>

#include "omp.h"

#include "algorithms/algorithms.h"
#include "network/protocol.h"
#include "network/server.h"
#include "utils/options.h"
#include "utils/file.h"

float* H = NULL;
int Hrows = 0;
int Hcols = 0;

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
    float *r = (float *)calloc(Hrows, sizeof(float));
    
    read_message(readStream, command, &algorithmIndex, r, Hrows);
    printf("Command: %s algorithmIndex: %i\n", command, algorithmIndex);
    
    float *f = (float *)calloc(Hcols, sizeof(float));
    float *p = (float *)calloc(Hcols, sizeof(float));

    printf("r[10000]: %e r[10001]: %e\n", r[10000], r[10001]);

    double time = omp_get_wtime();

    printf("CGNE begin\n");
    cgne(H, Hrows, Hcols, f, r, p);
    printf("CGNE end: %lf s\n", omp_get_wtime() - time);

    printf("wrote %i\n", write(connection->sock, f, Hcols*sizeof(float)));

    free(f);
    free(r);
    free(p);

    fclose(writeStream);
    fclose(readStream);

    close(connection->sock);
    free(connection);
}

int main(int argc, char **argv) {

    int sock = -1;

    {
        options_t options = {
            .address = "127.0.0.1",
            .port = 3145,
            .file = "../data/H-1.float",
            .Hrows = 50816,
            .Hcols = 3600
        };

        set_options(argc, argv, &options);
        Hrows = options.Hrows;
        Hcols = options.Hcols;

        int Hsize = Hrows*Hcols;
        H = (float *)calloc(Hsize, sizeof(float));

        double time = omp_get_wtime();
        import_bin(options.file, H, &Hsize);
        printf("Loaded H in %lf s\n", omp_get_wtime() - time);

        sock = create_server(options.address, options.port);

        if (sock < 0) {
            return sock;
        }

        printf("Listening on %s:%i...\n", options.address, options.port);
    }

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