#include "server.h"

void socket_error(int sock, char *value) {
    if (sock < 0) {
        printf("socket: failed to %s\n", value);
    }
}

int new_socket() {
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    socket_error(sock, "create");
    return sock;
}

int bind_socket(int sock, int port) {
    if (sock < 0) { return sock; }
    
    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    int result = bind(sock, (struct sockaddr *)&address, sizeof(struct sockaddr_in));
    socket_error(result, "bind");

    return result >= 0 ? sock : -2;
}

int listen_socket(int sock) {
    if (sock < 0) { return sock; }

    int result = listen(sock, 60);
    socket_error(result, "listen");

    return result >= 0 ? sock : -3;
}

int create_server() {
    int sock = new_socket();
    sock = bind_socket(sock, 3333);
    sock = listen_socket(sock);
    
    return sock;
}