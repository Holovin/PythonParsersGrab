#!/bin/bash
(crontab -l ; echo "00 02 * * * bash $PWD/run.sh") | crontab