# logger.py
# App logger initialization function
# r1
# TODO: logger.propagate using

import logging
from logging.handlers import RotatingFileHandler
from helpers.config import Config


def logger_setup(log_file, loggers=None, touch_root=False):
    log_formatter = logging.Formatter(Config.get('APP_LOG_FORMAT'), datefmt='%Y/%m/%d %H:%M:%S')
    work_mode = Config.get('APP_WORK_MODE')
    full_debug = Config.get('APP_CAN_OUTPUT')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(log_formatter)

    if work_mode == 'dev':
        log_level = logging.DEBUG
    elif work_mode == 'info':
        log_level = logging.INFO
    else:
        log_level = logging.ERROR

    root = logging.getLogger()

    if touch_root:
        root.setLevel(log_level)
        root.addHandler(logging.NullHandler())

        if full_debug == 'True':
            root.addHandler(console)
            root.info('Console output enabled')

    handler = RotatingFileHandler(log_file, backupCount=1, encoding='utf-8')
    handler.setLevel(log_level)
    handler.setFormatter(log_formatter)
    handler.doRollover()

    if loggers:
        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(log_level)
            logger.addHandler(handler)
            logger.propagate = False

            if full_debug == 'True':
                logger.addHandler(console)
    else:
        root.warning('Empty loggers list')
