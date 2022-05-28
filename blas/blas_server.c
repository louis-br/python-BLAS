#include <stdio.h>
#include <stdlib.h>
#include <string.h>
//#include <pthread.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <linux/in.h>
#include <unistd.h>

#include "omp.h"
#include "mkl.h"

typedef struct
{
	int sock;
	struct sockaddr address;
	int addr_len;
} connection_t;

float* H;

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

void cgne(float *H, float *f, float *r, float *p) {
    /*MKL_INT         m, n, lda, incx, incy;
    MKL_INT         rmaxa, cmaxa;
    float           alpha, beta;
    float          *a, *x, *y;
    CBLAS_LAYOUT    layout;
    CBLAS_TRANSPOSE trans;
    MKL_INT         nx, ny, len_x, len_y;*/
    //printf("1\n");
    //memcpy(r, g, 50816*sizeof(float));
    //printf("2\n");
    //          Layout,        TransA,       M,    N,    alpha,  A, lda,  X, incX, beta, Y, incY
    cblas_sgemv(CblasRowMajor, CblasNoTrans, 50816, 3600, -1.0F, H, 3600, f, 1,    1.0F, r, 1);
    //printf("3\n");
    cblas_sgemv(CblasRowMajor, CblasTrans,   50816, 3600, 1.0F,  H, 3600, r, 1,    0.0F, p, 1);
    //printf("4\n");
    for (int i = 0; i < 100; i++) {
        //                            N,     X, incX, Y, incY
        float rdot =       cblas_sdot(50816, r, 1,    r, 1);
        //printf("5\n");
        float alpha = rdot/cblas_sdot(3600, p, 1,    p, 1);
        //printf("6 rdot: %f pdot: %f alpha:%f\n", rdot, pdot, alpha);
        //          N, alpha, X, incX, Y, incY
        cblas_saxpy(3600, alpha, p, 1, f, 1);
        //printf("7\n");
        //          Layout,        TransA,       M,    N,    alpha,    A, lda,  X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasNoTrans, 50816, 3600, -alpha,  H, 3600, p, 1,    1.0F, r, 1);
        //printf("8\n");
        //                      N,     X, incX, Y, incY
        float beta = cblas_sdot(50816, r, 1,    r, 1)/rdot;
        //printf("9 beta: %f\n", beta);
        //          Layout,        TransA,     M,     N,    alpha, A, lda,  X, incX, beta, Y, incY
        cblas_sgemv(CblasRowMajor, CblasTrans, 50816, 3600, 1.0F,  H, 3600, r, 1,    beta, p, 1);
        //printf("10\n");
    }
}

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

void process(connection_t *connection) {
    FILE *readStream = NULL;
    FILE *writeStream = NULL;
    {
        int writeSock = dup(connection->sock);
        if (writeSock < 0) { printf("Failed to duplicate socket\n"); return; }
        writeStream = fdopen(writeSock, "w");
    }
    readStream = fdopen(connection->sock, "r");
    setvbuf(readStream, NULL, _IONBF, 0);

    if (readStream == NULL || writeStream == NULL) { printf("Failed to create stream\n"); return; }

    char command[32] = "";
    int algorithmIndex = 0;
    float *r = (float *)calloc(50816, sizeof(float));
    
    read_message(readStream, (char *)&command, &algorithmIndex, r);
    printf("Command: %s algorithmIndex: %i\n", command, algorithmIndex);
    
    float *f = (float *)calloc(3600, sizeof(float));
    float *p = (float *)calloc(3600, sizeof(float));

    /*int size = 50816*sizeof(float);
    int offset = 0;

    while (offset < size) {
        printf("offset: %d\n", offset);
        offset += read(connection->sock, ((void *)r + offset), size - offset);
    }*/

    printf("r[10000]: %e r[10001]: %e\n", r[10000], r[10001]);

    printf("CGNE begin\n");
    cgne(H, f, r, p);
    printf("CGNE end\n");

    printf("wrote %i\n", write(connection->sock, f, 3600*sizeof(float)));

    free(f);
    free(r);
    free(p);

    fclose(writeStream);
    fclose(readStream);

    close(connection->sock);
    free(connection);
}

int main()
{
    int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock < 0) {
        printf("Failed to create socket\n");
        return -1;
    }

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(3333);
    if (bind(sock, (struct sockaddr *)&address, sizeof(struct sockaddr_in)) < 0) {
        printf("Failed to bind socket\n");
        return -2;
    }

    if (listen(sock, 60) < 0) {
        printf("Failed to listen\n");
        return -3;
    }

    H = (float *)calloc(50816*3600, sizeof(float));

    read_csv("../data/H-1.csv", H, 50816*3600);
    printf("Done reading csv: H\n");

    #pragma omp parallel
    {
        #pragma omp single nowait
        while (1) {
            connection_t *connection = (connection_t*)malloc(sizeof(connection_t));
            connection->sock = accept(sock, &connection->address, &connection->addr_len);
            printf("got connection\n");
            if (connection->sock <= 0) {
                free(connection);
            } else {//single nowait
                #pragma omp task untied
                {
                    process(connection);
                }
                //pthread_t thread;
                //pthread_create(&thread, 0, process, (void *)connection);
                //pthread_detach(thread);
            }
        }
    }

    free(H);
    
    return 0;
}