## Installation
### 1. Dependencies
`sudo apt install python-pip python-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev`

### 2. Install
```bash
cd ~
wget -O python.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash python.sh -b
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
```

