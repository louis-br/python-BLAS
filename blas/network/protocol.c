#include "protocol.h"

typedef struct
{
    int size;
    int maxSize;
    char key[32];
    char* value;
} field_t;

void read_error(char *field, char *value) {
    printf("Failed to read %s: %s\n", field, value);
}

void write_error(char *field, char *value) {
    printf("Failed to write %s: %s\n", field, value);
}

int create_streams(int sock, streams_t *streams) {
    FILE *readStream = NULL;
    FILE *writeStream = NULL;
    {
        int writeSock = dup(sock);
        if (writeSock < 0) { printf("Failed to duplicate socket\n"); return -1; }
        writeStream = fdopen(writeSock, "w");
    }
    readStream = fdopen(sock, "r");
    setvbuf(readStream, NULL, _IONBF, 0);
    setvbuf(writeStream, NULL, _IONBF, 0);

    if (readStream == NULL || writeStream == NULL) { printf("Failed to create streams\n"); return -1; }
    
    streams->read = readStream;
    streams->write = writeStream;

    return 0;
}

int discard(FILE* read, int n) {
    printf("discard: %i\n", n);
    int bufferSize = n > MAX_BUFFER_SIZE ? MAX_BUFFER_SIZE : n;
    char *temp = (char*)malloc(bufferSize*sizeof(char));
    while (n > 0) {
        int left = n > bufferSize ? bufferSize : n;
        printf("left: %i\n", left);
        int err = fread(temp, left, 1, read);
        if (err != 1) { printf("err: %d\n", err); return -1; }
        n -= left;
    }
    free(temp);
    return 0;
}

int read_fields(FILE* read, field_t *fields, int maxFields) {

    int fieldsReceived = 0;
    if (fread(&fieldsReceived, sizeof(int), 1, read) != 1) { read_error("fieldsReceived", ""); return -1; }

    for (int i = 0; i < fieldsReceived; i++) {
        char fieldName[32] = "";
        int fieldNameSize = 0;
        int fieldSize = 0;

        if (fread(&fieldNameSize, sizeof(int), 1, read) != 1) { read_error("?", "fieldNameSize"); return -1; }
        fieldNameSize = fieldNameSize < 32 ? fieldNameSize : 31;

        if (fread(&fieldName, sizeof(char), fieldNameSize, read) != fieldNameSize) { read_error("?", "fieldName"); return -1; }
        if (fread(&fieldSize, sizeof(int), 1, read) != 1) { read_error(fieldName, "fieldSize"); return -1; }

        int skip = 1;
        for (int currentField = 0; currentField < maxFields; currentField++) {
            if (strncmp(fieldName, fields[currentField].key, 32) == 0) {
                if (fields[currentField].value == NULL) {
                    break;
                }
                if (fieldSize > fields[currentField].maxSize || fields[currentField].size != 0 && fields[currentField].size != fieldSize) {
                    printf("field bad size: %s\n", fieldName);
                    break;
                }
                
                if (fread(fields[currentField].value, fieldSize, 1, read) != 1) { read_error(fieldName, "value"); return -1; }
                skip = 0;
                break;
            }
        }

        if (skip) {
            printf("Skipping %s...\n", fieldName);
            if (discard(read, fieldSize) < 0) { read_error(fieldName, "discard"); return -1; }
        }
    }
    return 0;
}

int read_message(streams_t *streams, input_message_t *message) {
    int arrayGsize = message->arrayGsize;

    field_t fields[] = {
        {0,                         sizeof(char[32]),           "command",          (char *)&message->command      },
        {sizeof(int),               sizeof(int),                "algorithmIndex",   (char *)&message->algorithmType},
        {arrayGsize*sizeof(float),  arrayGsize*sizeof(float),   "arrayG",           (char *)message->arrayG        },
        {sizeof(int),               sizeof(int),                "maxIterations",    (char *)&message->maxIterations},
        {sizeof(float),             sizeof(float),              "minError",         (char *)&message->minError     }
    };

    return read_fields(streams->read, fields, sizeof(fields)/sizeof(field_t));
}

int write_fields(FILE* write, field_t *fields, int maxFields) {
    if (fwrite(&maxFields, sizeof(int), 1, write) != 1) { write_error("maxFields", ""); return -1; }
    for (int i = 0; i < maxFields; i++) {
        char *key = fields[i].key;
        int keyLength = strlen(key);
        if (fwrite(&keyLength, sizeof(int), 1, write) != 1) { write_error(key, "fieldNameSize"); return -1; }
        if (fwrite(key, keyLength, 1, write) != 1) { write_error(key, "fieldName"); return -1; }
        if (fwrite(&(fields[i].size), sizeof(int), 1, write) != 1) { write_error(key, "fieldSize"); return -1; }
        //printf("writing %s: %i bytes\n", key, fields[i].size);
        if (fwrite(fields[i].value, fields[i].size, 1, write) != 1) { write_error(key, "value"); return -1; }
    }
}

int write_message(streams_t *streams, output_message_t *message) {
    int arrayFsize = message->arrayFsize;

    field_t fields[] = {
        {arrayFsize*sizeof(float),  arrayFsize*sizeof(float),   "arrayF",           (char *)message->arrayF        },
        {sizeof(int),               sizeof(int),                "iterations",       (char *)&message->iterations   }
    };

    return write_fields(streams->write, fields, sizeof(fields)/sizeof(field_t));
}