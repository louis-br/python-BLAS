MKL_LIB = /opt/conda/pkgs/mkl-static-2022.1.0-intel_223/lib
MKL_INCLUDE = /opt/conda/pkgs/mkl-include-2022.1.0-intel_223/include

all:
	gcc main.c algorithms/algorithms.c network/protocol.c network/server.c utils/file.c utils/options.c utils/shutdown.c -o out/blas \
		-Wl,--start-group ${MKL_LIB}/libmkl_intel_lp64.a ${MKL_LIB}/libmkl_gnu_thread.a ${MKL_LIB}/libmkl_core.a $(shell gcc --print-file-name=libgomp.a) -Wl,--end-group \
		-lgomp -fopenmp -lpthread -lm -ldl -m64 -I"${MKL_INCLUDE}"
