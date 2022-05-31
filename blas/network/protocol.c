#include "protocol.h"

void read_error(char *value) {
    printf("Failed to read %s\n", value);
}

size_t discard(FILE *stream, int bytes) {
    int bufferSize = bytes < 50816*sizeof(float) ? bytes : 50816*sizeof(float);
    char *temp = (char*)malloc(bytes*sizeof(char));
    size_t result = 0;
    while (bytes >= bufferSize) {
        printf("skip loop\n");
        result = fread(temp, bufferSize, 1, stream);
        if (result != 1) { free(temp); return result; }
        bytes -= bufferSize;
    }
    result = fread(temp, bytes, 1, stream);
    free(temp);
    return result;
}

//setvbuf
int read_message(FILE *stream, char *command, int *algorithmIndex, float *arrayG) {
    typedef struct {int size; int maxSize; char key[32]; char* value;} field_t;
    field_t fields[] = {
        {0,                      sizeof(char[32]),    "command",         (char *)command},
        {sizeof(int),            sizeof(int),         "algorithmIndex",  (char *)algorithmIndex},
        {50816*sizeof(float),    50816*sizeof(float), "arrayG",          (char *)arrayG}
    };

    int maxFields = sizeof(fields)/sizeof(field_t);
    int fieldsReceived = 0;
    char fieldName[32] = "";

    if (fread(&fieldsReceived, sizeof(int), 1, stream) != 1) { read_error("fieldsReceived"); return -1; }
    for (int i = 0; i < fieldsReceived; i++) {
        printf("field loop\n");
        int fieldNameSize = 0;
        int fieldSize = 0;

        if (fread(&fieldNameSize, sizeof(int), 1, stream) != 1) { read_error("fieldNameSize"); return -1; }
        fieldNameSize = fieldNameSize < 32 ? fieldNameSize : 31;

        if (fread(&fieldName, sizeof(char), fieldNameSize, stream) != fieldNameSize) { read_error("fieldName"); return -1; }
        if (fread(&fieldSize, sizeof(int), 1, stream) != 1) { read_error("fieldSize"); return -1; }

        int skip = 1;
        for (int currentField = 0; currentField < maxFields; currentField++) {
            if (strncmp(fieldName, fields[currentField].key, 32) == 0) {
                printf("fieldsReceived: %i fieldName: %s fieldNameSize: %i fieldSize: %i currentField: %i\n", fieldsReceived, fieldName, fieldNameSize, fieldSize, currentField);
                if (fields[currentField].value == NULL) {
                    break;
                }
                if (fieldSize > fields[currentField].maxSize || fields[currentField].size != 0 && fields[currentField].size != fieldSize) {
                    printf("Skipping field %s: wrong size\n", fieldName);
                    break;
                }
                
                if (fread(fields[currentField].value, fieldSize, 1, stream) != 1) { read_error(fieldName); return -1; }
                skip = 0;
                break;
            }
        }

        if (skip) {
            printf("Skipping...\n");
            if (discard(stream, fieldSize) != 1) { read_error(fieldName); return -1; }
        }
    }
    return 0;
}