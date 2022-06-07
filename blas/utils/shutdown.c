#include "shutdown.h"

volatile int SERVER_RUNNING = 1;

void handler(int signum) {
    if (signum == SIGINT || signum == SIGTERM) {
        #pragma omp atomic write
        SERVER_RUNNING = 0;
    }
}

void stop() {
    #pragma omp atomic write
    SERVER_RUNNING = 0;
    raise(SIGTERM);
}

void setup_signals() {
    struct sigaction action = {
        .sa_flags = 0,
        .sa_handler = &handler
    };

    sigemptyset(&action.sa_mask);
    sigaction(SIGINT, &action, NULL);
    sigaction(SIGTERM, &action, NULL);
}