# DParsers-Grab-Core (v2.9)
Common core for site parsing with python grab framework.

## Install Python (pre-install)
1. Install Python 3.6 (or newer)
```
wget -O python.sh https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash python.sh -b
rm python.sh
export PATH=~/miniconda3/bin:$PATH
```
2. Install [pipenv](https://github.com/pypa/pipenv) (`pip install pipenv`)

## Project install
1. Clone project
2. In project directory `pipenv install`
3. \[Optional for Windows\] Download and install [curl](https://chocolatey.org/packages/curl/)

## Running
1. Run `pipenv shell` 
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
