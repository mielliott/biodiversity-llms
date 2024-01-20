#/bin/bash

conda install -n base -c conda-forge mamba
mamba env create --name centra7 --file environment.yml
mamba activate centra7
mamba env update --prune
