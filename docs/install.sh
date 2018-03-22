#!/bin/bash
cd ~
wget -O python.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash python.sh -b
rm python.sh

export PATH=~/miniconda3/bin:$PATH
conda create --name 'd_parsers' python=3.6 -y
source activate d_parsers

pip install grab python-dotenv -q
conda install pycurl

source deactivate
