import logging
from logging.handlers import RotatingFileHandler

from helpers.config import Config


def logger_setup(log_file, loggers=None, touch_root=False):
    log_formatter = logging.Formatter(Config.get('APP_LOG_FORMAT'), datefmt='%Y/%m/%d %H:%M:%S')

    mode = Config.get('APP_WORK_MODE')
    full_debug = Config.get('APP_CAN_OUTPUT')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(log_formatter)

    if mode == 'dev':
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    if touch_root:
        root = logging.getLogger()
        root.setLevel(log_level)
        root.addHandler(logging.NullHandler())

        if full_debug == 'True':
            root.addHandler(console)

    handler = RotatingFileHandler(log_file, backupCount=1)
    handler.setLevel(log_level)
    handler.setFormatter(log_formatter)
    handler.doRollover()

    if loggers is None:
        loggers = []

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)
        logger.propagate = False

        if full_debug == 'True':
            logger.addHandler(console)
