#include "options.h"

int set_options(int argc, char **argv, options_t *options) {
    int caseID = 0;

    static struct option long_options[] =
    {
        {"address",   required_argument, 0, 'a'},
        {"port",      required_argument, 0, 'p'},
        {"file",      required_argument, 0, 'f'},
        {"rows",      required_argument, 0, 'r'},
        {"columns",   required_argument, 0, 'c'},
        {"help",      no_argument,       0, 'h'},
        {0, 0, 0, 0}
    };

    while ((caseID = getopt_long(argc, argv, "a:p:h", long_options, NULL)) != -1) {
        switch (caseID)
        {
            case 'a':
                strncpy(options->address, optarg, ADDRESS_SIZE - 1);
                break;
            case 'p':
                options->port = strtol(optarg, NULL, 0);
                break;
            case 'f':
                strncpy(options->file, optarg, PATH_MAX - 1);
                break;
            case 'r':
                options->Hrows = strtol(optarg, NULL, 0);
                break;
            case 'c':
                options->Hcols = strtol(optarg, NULL, 0);
                break;
            case 'h':
                printf("Usage: %s [options]\n\
                options:\n\
                    -a, --address   IP address to listen\n\
                    -p, --port      port to listen\n\
                    -f, --file      path to the H matrix .float file\n\
                    -r, --rows      rows of the H matrix\n\
                    -c, --columns   columns of the H matrix\n\
                    -h, --help      prints this help\n", argv[0]);
                exit(0);
                break;
        }
    }

    return 0;
}