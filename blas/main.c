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
    int tid = omp_get_thread_num();
    
    streams_t streams = {NULL, NULL};    
    create_streams(connection->sock, &streams);

    float *r = (float *)calloc(Hrows, sizeof(float));
    
    input_message_t input = {
        .command = "",
        .algorithmType = 0,
        .arrayG = r,
        .arrayGsize = Hrows
    };

    read_message(&streams, &input);
    printf("[%i] Command: %s algorithmIndex: %i\n", tid, input.command, input.algorithmType);
    
    float *f = (float *)calloc(Hcols, sizeof(float));
    float *p = (float *)calloc(Hcols, sizeof(float));

    double time = omp_get_wtime();

    printf("[%i] CGNE begin r[%i]: %e\n", tid, 10000, 10000);
    cgne(H, Hrows, Hcols, f, r, p);
    printf("[%i] CGNE end: %lf s\n", tid, omp_get_wtime() - time);

    printf("[%i] wrote %i\n", tid, write(connection->sock, f, Hcols*sizeof(float)));

    free(r);
    free(f);
    free(p);

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