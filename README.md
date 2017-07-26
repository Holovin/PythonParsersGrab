# D_GrabDemo
Simple app for parse site with grab python framework

## Install environment
With `pip` (or `conda`):
1. Create new environment: `virtualenv $ENVIRONMENT_NAME` (or `conda create --name $ENVIRONMENT_NAME python`)
1. Install packages: `pip install -r requirements.txt`
1. Activate environment: `source $ENV_BASE_DIR/$ENVIRONMENT_NAME/bin/activate` or (`source activate $ENVIRONMENT_NAME`)
1. Run script `python3 main.py`

## Config .env description
- `SITE_URL_{NUMBER}` - site url's for parse
- `SITE_PAGE_PARAM` - page param for iterate
- `APP_OUTPUT_DIR` - output dir
- `APP_OUTPUT_ENC` - output encoding
- `APP_THREAD_COUNT` - count of threads for grub.spider
- `APP_LOG_FORMAT` - log format (in python logger format)
- `APP_LOG_FILE` - path to log file
- `APP_WORK_MODE` - `dev` value sets DEBUG mode for all loggers, otherwise INFO 
- `APP_TRY_LIMIT` - number of repeat tasks
