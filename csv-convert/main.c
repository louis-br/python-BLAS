#include "file.h"

int main(int argc, char **argv) {
    if (argc != 5) {
        printf("More arguments needed\n");
        return -1;
    }
    int size = atoi(argv[1])*atoi(argv[2]);
    float *H = (float *)calloc(size, sizeof(float));

    import_csv(argv[3], H, size);
    export_bin(argv[4], H, size);
    
    return 0;
}