#!/bin/sh
conda create --prefix /tmp/env --clone base
sudo bash -c '. /opt/conda/bin/activate && conda install -c conda-forge conda-pack --yes'
conda-pack --n-threads -1 --compress-level 9 --prefix /tmp/env --output env.tar.gz
#sudo apt update && sudo apt install pigz
#tar --use-compress-program="pigz -k -9" -cvzf env.tar.gz /tmp/env
#docker run --platform linux/amd64 -v "$(pwd)/utils/package/env.tar.gz:/env.tar.gz:ro" -t -i --rm ubuntu bash
#conda env create -p /tmp/package -f environment.yml
#conda env remove --prefix /tmp/env