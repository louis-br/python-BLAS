#include "file.h"

int import_csv(char *filename, float *array, int arraySize) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        printf("Cannot open file: %s\n", filename);
        return 0;
    }

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
        if (i > arraySize) {
            printf("Array too small\n");
            return 0;
        }
    }

    return fclose(file) + 1;
}

int import_bin(char *filename, float *array, int *arraySize) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        printf("Cannot open file: %s\n", filename);
        return 0;
    }

    fseek(file, 0, SEEK_END);
    long size = ftell(file);
    rewind(file);

    if (arraySize == NULL || array == NULL) {
        array = (float *)malloc(size*sizeof(char));
    }
    else if (*arraySize < size*sizeof(char)) {
        array = (float *)realloc(array, size*sizeof(char));
    }

    if (array == NULL) {
        printf("Cannot allocate memory: %s\n", filename);
        return 0;
    }

    *arraySize = size/sizeof(float);

    if (fread(array, sizeof(char), size, file) != size) {
        printf("Error copying to memory\n");
        return 0;
    }

    return fclose(file) + 1;
}

int export_bin(char *filename, float *array, int arraySize) {
    FILE *file = fopen(filename, "w");
    if (file == NULL) {
        printf("Cannot open file: %s\n", filename);
        return 0;
    }

    if (fwrite(array, sizeof(float), arraySize, file) != arraySize) {
        printf("Error writing to file: %s\n", filename);
        return 0;
    }

    return fclose(file) + 1;
}