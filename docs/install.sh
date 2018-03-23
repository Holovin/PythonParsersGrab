#!/bin/bash
cd ~
wget -O python.sh https://repo.continuum.io/archive/Anaconda3-5.1.0-Linux-x86_64.sh
bash python.sh -b
rm python.sh

export PATH=~/anaconda3/bin:$PATH
conda create --name 'd_parsers' python=3.6 -y
source activate d_parsers

pip install grab python-dotenv -q
conda install pycurl

source deactivate
