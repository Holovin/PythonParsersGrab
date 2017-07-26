# DParsers-Grab-EKC
App for parse site \*\*\*\*\*\*\*.\*\* with python grab framework.

## Install environment
1. Install libs: `sudo bash pre_install_need_sudo.sh`
1. Install miniconda (python env) and libs: `bash install.sh`

##### Add to crontab
1. Run `bash add_crontab.sh` for add `bash run.sh` (with current path) to crontab (default time see in bash script)

## Running
1. Run `bash run.sh`

## Config .env description
##### Primary params
- `SITE_URL_{NUMBER}` - site url's for parse
- `SITE_PAGE_PARAM` - page param for iterate
- `APP_THREAD_COUNT` - count of threads for grub.spider
- `APP_OUTPUT_DIR` - output dir
- `APP_OUTPUT_ENC` - output encoding

##### Secondary params
- `APP_LOG_FORMAT` - log format (in python logger format)
- `APP_LOG_DEBUG_FILE` - path to log file (only own code output)
- `APP_LOG_GRUB_FILE` - path to log file (only grub lib output)
- `APP_WORK_MODE` - `dev` value sets DEBUG mode for all loggers, otherwise INFO 
- `APP_TRY_LIMIT` - number of repeat tasks
