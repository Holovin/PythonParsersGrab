# DParsers-Grab-Core (v2)
Common core for site parsing with python grab framework.

## Installation (for clean Ubuntu Server 16.04)
1. Run `sudo bash docs/pre_install_need_sudo.sh`
1. Run `bash docs/install.sh`

## Config .env description
- `ENV_FILE` - env filename to load site specific config
- `APP_WORK_MODE` - `dev` value sets DEBUG mode for all loggers, otherwise will set INFO
- `APP_CAN_OUTPUT` - `True` allows to `print(...)` some important messages
- `APP_LOG_FORMAT` - log format (in python logger format)
- `APP_LOG_DEBUG_FILE` = path to log file (only own code output)
- `APP_LOG_GRAB_FILE` =  path to log file (only grab lib output)

## Config {site}.env description
- `APP_THREAD_COUNT` - count of threads for grub.spider
- `APP_TRY_LIMIT` - how many times app can repeat failed task
- `SITE_URL_{NUMBER}` - site url's for parse
- `SITE_PAGE_PARAM` - page param for iterate
- `APP_OUTPUT_DIR` - output dir
- `APP_OUTPUT_ENC` - output encoding
- `APP_COOKIE_NAME` and `APP_COOKIE_VALUE` - if exist and non-empty - set this cookie before all requests

