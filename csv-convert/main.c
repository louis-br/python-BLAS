#include "file.h"

int main() {
    float *H = (float *)calloc(50816*3600, sizeof(float));

    import_csv("../data/H-1.csv", H, 50816*3600);
    export_bin("../data/H-1.float", H, 50816*3600);
    
    return 0;
}