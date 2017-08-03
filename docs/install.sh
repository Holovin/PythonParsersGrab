#!/bin/bash
cd ~
wget -O python.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash python.sh -b
rm python.sh

export PATH=~/miniconda3/bin:$PATH
conda create --name 'd_parsers' python=3.6 -y
source activate d_parsers

pip install grab python-dotenv -q

# fix bug
# libcurl link-time version (...) is older than compile-time version (...)
pip uninstall pycurl -q
export LD_LIBRARY_PATH=/usr/local/opt/curl/lib
export LIBRARY_PATH=/usr/local/opt/curl/lib
easy_install pycurl

source deactivate