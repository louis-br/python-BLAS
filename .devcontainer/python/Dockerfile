FROM continuumio/miniconda3:4.11.0
#RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
#RUN bash ~/miniconda.sh -b -f -p /usr/local/
RUN conda init
RUN conda update conda --yes
#eval "$(/miniconda/bin/conda shell.bash hook)"
RUN conda install scipy --yes
RUN conda install ipykernel --yes
RUN conda install matplotlib --yes
RUN conda install pandas --yes
#--update-deps --force-reinstall