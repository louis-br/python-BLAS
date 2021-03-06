#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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
#include "utils/shutdown.h"

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
        .arrayGsize = Hrows,
        .maxIterations = 1000,
        .minError = 1e-10
    };

    read_message(&streams, &input);
    
    float *f = (float *)calloc(Hcols, sizeof(float));
    double time = omp_get_wtime();

    printf("[%i] [%i] %s begin\n", Hrows, tid, input.algorithmType == 1 ? "CGNR" : "CGNE");

    int iterations = input.algorithmType == 1 ?
                     cgnr(input.maxIterations, input.minError, H, Hrows, Hcols, f, r) :
                     cgne(input.maxIterations, input.minError, H, Hrows, Hcols, f, r);
        
    printf("[%i] [%i] %s end: iterations %i: %lf s\n", Hrows, tid, input.algorithmType == 1 ? "CGNR" : "CGNE", iterations, omp_get_wtime() - time);

    output_message_t output = {
        .arrayF = f,
        .arrayFsize = Hcols,
        .iterations = iterations
    };

    write_message(&streams, &output);

    free(r);
    free(f);
    close(connection->sock);
    free(connection);
}

int main(int argc, char **argv) {

    int sock = -1;

    {
        options_t options = {
            .address = "127.0.0.1",
            .port = 3145,
            .file = "../utils/data/H-1.float",
            .Hrows = 50816,
            .Hcols = 3600
        };

        set_options(argc, argv, &options);
        setup_signals();

        sock = create_server(options.address, options.port);

        if (sock < 0) {
            return sock;
        }

        printf("Listening on %s:%i...\n", options.address, options.port);

        Hrows = options.Hrows;
        Hcols = options.Hcols;
        int Hsize = Hrows*Hcols;
        H = (float *)calloc(Hsize, sizeof(float));

        double time = omp_get_wtime();

        int loaded = import_bin(options.file, H, &Hsize);

        if (Hsize != Hrows*Hcols || loaded <= 0) {
            printf("Failed to load H: got %i, expected: %i\n", Hsize, Hrows*Hcols);
            close(sock);
            free(H);
            exit(EXIT_FAILURE);
        }

        printf("Loaded H in %lf s\n", omp_get_wtime() - time);
    }

    #pragma omp parallel default(none) shared(sock) shared(H) shared(Hrows) shared(Hcols) shared(SERVER_RUNNING)
    {
        #pragma omp single nowait
        {
            int running = 1;
            while (running) {
                connection_t *connection = (connection_t*)malloc(sizeof(connection_t));
                connection->sock = accept(sock, &connection->address, &connection->addr_len);
                if (connection->sock <= 0) {
                    free(connection);
                } else {
                    #pragma omp task untied
                    {
                        process(connection);
                    }
                }
                #pragma omp atomic read
                running = SERVER_RUNNING;
            }
        }
    }

    close(sock);
    free(H);
    
    return 0;
}