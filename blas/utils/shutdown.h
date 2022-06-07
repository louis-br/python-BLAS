#include <stdlib.h>
#include <signal.h>

#ifndef SHUTDOWN_H
#define SHUTDOWN_H

extern volatile int SERVER_RUNNING;

void stop();
void setup_signals();

#endif