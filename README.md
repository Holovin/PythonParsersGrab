# D_GrabDemo
Simple app for parse site with grab python framework

## Install environment
With `pip` (or `conda`):
1. Create new environment: `virtualenv $ENVIRONMENT_NAME` (or `conda create --name $ENVIRONMENT_NAME python`)
1. Install packages: `pip install -r requirements.txt`
1. Activate environment: `source $ENV_BASE_DIR/$ENVIRONMENT_NAME/bin/activate` or (`source activate $ENVIRONMENT_NAME`)
1. Run script `python3 main.py`

## Config .env description
- `SITE_URL` - site url for parse 
- `SITE_PAGE_PARAM` - page param for iterate
- `APP_OUTPUT_CSV` - parse result file
- `APP_THREAD_COUNT` - count of threads for grub.spider
- `APP_LOG_FORMAT` - log format (in python logger format)
- `APP_LOG_FILE` - path to log file
- `APP_WORK_MODE` - `dev` value sets DEBUG mode for all loggers, otherwise INFO 

## Requirements
- `Python 3.6.1`

### Conda list
`lxml=3.8.0=py36_0
pip=9.0.1=py36_1
pycurl=7.43.0=py36_2
python=3.6.1=2
setuptools=27.2.0=py36_1
wheel=0.29.0=py36_0`

### Pip freeze
`click==6.7
defusedxml==0.5.0
grab==0.6.38
lxml==3.8.0
pycurl==7.43.0
python-dotenv==0.6.4
pytils==0.3
selection==0.0.13
six==1.10.0
user-agent==0.1.8
weblib==0.1.24`
