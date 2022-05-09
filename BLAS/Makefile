MKL_LIB = /opt/conda/pkgs/mkl-static-2022.1.0-intel_223/lib
MKL_INCLUDE = /opt/conda/pkgs/mkl-include-2022.1.0-intel_223/include

all:
	gcc blas_server.c -o blas -Wl,--start-group ${MKL_LIB}/libmkl_intel_lp64.a ${MKL_LIB}/libmkl_sequential.a ${MKL_LIB}/libmkl_core.a -Wl,--end-group -lpthread -lm -ldl -m64 -I"${MKL_INCLUDE}"
