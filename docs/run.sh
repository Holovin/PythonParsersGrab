#!/bin/bash
export PATH=~/miniconda3/bin:$PATH
source activate d_parsers
python main.py
source deactivate