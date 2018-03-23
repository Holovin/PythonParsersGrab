#!/bin/bash
echo 'You need specify site config name (example: python main.py test.env)'
export PATH=~/anaconda3/bin:$PATH
source activate d_parsers
python ../main.py
source deactivate