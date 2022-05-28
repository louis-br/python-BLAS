#include "file.h"

int read_csv(char *filename, float *array, int length) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        printf("Cannot open file: %s\n", filename);
        return 0;
    }

    /*FILE *file;

    fseek(disk, 0, SEEK_END);
    long size = ftell(disk);
    rewind(disk);
    char *buffer = (char *)malloc(size*sizeof(char));
    if (buffer != NULL) {
        if (fread(buffer, sizeof(char), size, disk) != size) {
            printf("Error copying to memory\n");
            return 0;
        }
        file = fmemopen(buffer, size*sizeof(char), "r");
        fclose(disk);
    } else {
        printf("Not enough memory for the whole file\n");
        file = disk;
    }

    printf("Size: %ld\n", size);*/

    float f;
    int i = 0;
    int c = 0;
    while (c >= 0) {
        c = fscanf(file, "%f%*[,;\n\r]", &f);
        if (c == EOF) {
            return 0;
        }
        if (c == 0) {
            printf("Failed to load float after: %e, read: %i bytes\n", f, c);
            return 0; 
        }
        array[i] = f;
        i += c;
        if (i > length) {
            printf("Array too small\n");
            return 0;
        }
    }

    return fclose(file) + 1;
}