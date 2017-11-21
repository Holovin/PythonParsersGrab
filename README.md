# DParsers-Grab-Core (v2.4.1-beta)
Common core for site parsing with python grab framework.

## Installation (for clean Ubuntu Server 16.04)
1. Run `sudo bash docs/pre_install_need_sudo.sh`
1. Run `bash docs/install.sh`

## Running
1. Run `python main.py {SITE_CONFIG_FILE_NAME}`

## Config .env description
- `APP_WORK_MODE` - `dev` value sets DEBUG mode for all loggers, otherwise will set INFO
- `APP_CAN_OUTPUT` - `True` allows to `print(...)` some important messages
- `APP_LOG_FORMAT` - log format (in python logger format)
- `APP_LOG_DIR` - log directory name
- `APP_LOG_DEBUG_FILE` - log file name (only own code output)
- `APP_LOG_GRAB_FILE` - log file name(only grab lib output)
- `APP_LOG_HTML_ERR` - output html in log when occur any exception
- `APP_STOCK_ZERO`, `APP_PRICE_ON_REQUEST` - parser consts

## Config {site}.env description
- `APP_PARSER` - name of file which store parser logic (Spider extended class)
- `APP_THREAD_COUNT` - count of threads for grub.spider
- `APP_TRY_LIMIT` - how many times app can repeat failed task
- `APP_COOKIE_NAME` and `APP_COOKIE_VALUE` - if exist and non-empty - set this cookie before all requests
- `APP_OUTPUT_CAT` - save file mode: '' (empty) for single file, 'test' - for separate result data to single files by 'test' result fields
- `APP_OUTPUT_DIR` - output dir
- `APP_OUTPUT_ENC` - output encoding
- `SITE_URL_{NUMBER}` - site url's for parse
- `SITE_PAGE_PARAM` - page param for iterate
