# DParsers-Grab-Core (v2.9)
Common core for site parsing with python grab framework.

## Installation (for clean Ubuntu Server 16.04)
1. Run `sudo bash docs/pre_install_need_sudo.sh`
1. Run `bash docs/install.sh`

## Running
1. Run `source activate d_parsers` 
1. Run `python main.py {SITE_CONFIG_FILE_NAME}`

## Base config .env description
- ! all values must be strings! -
- `APP_WORK_MODE` - `dev` value sets DEBUG mode for all loggers, supports `info` value, otherwise set `error`
- `APP_CAN_OUTPUT` - `True` allows to `print(...)` some important messages
- `APP_LOG_FORMAT` - log format (in python logger format)
- `APP_LOG_DIR` - log directory name
- `APP_LOG_DEBUG_FILE` - log file name (only own code output)
- `APP_LOG_GRAB_FILE` - log file name(only grab lib output)
- `APP_LOG_HTML_ERR` - output html in log when occur any exception
- `APP_CACHE_ENABLED` - enable page caching to your db (any value to enable)
- `APP_CACHE_DB_HOST` - db host
- `APP_CACHE_DB_PORT` - db post (default = 3306)
- `APP_CACHE_DB_TYPE` - db type (support mysql, mongo and some others - look grab docs)
- `APP_CACHE_DB_USER` - db user
- `APP_CACHE_DB_PASS` - db password

## Base config {site}.env description/
- `APP_PARSER` - name of file which store parser logic (Spider extended class)
- `APP_THREAD_COUNT` - count of threads for grub.spider
- `APP_TRY_LIMIT` - how many times app can repeat failed task
- `APP_SAVER_CLASS` - save to CSV or JSON format (or you can write own saver) [can occur crash when use csv with nested dicts]
- `APP_OUTPUT_CAT` - save file mode: '' (empty) for single file (and same behaviour when this property not defined), 'test' - for separate result data to single files by 'test' result fields
- `APP_OUTPUT_DIR` - output dir
- `APP_OUTPUT_ENC` - output encoding [default 'utf-8']
- `APP_SAVE_FIELDS_{NUMBER}` - string name fields for save in file (other fields dropped, even if parsed)
- `APP_COOKIE_NAME` and `APP_COOKIE_VALUE` (both optional) - set this cookie before all requests
- `SITE_URL_{NUMBER}` - site url's for parse
