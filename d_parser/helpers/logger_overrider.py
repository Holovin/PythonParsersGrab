import logging


class Log:
    def __init__(self, logger):
        self.logger = logger

    def critical(self, task, message):
        self.__write(logging.CRITICAL, task, message)

    def fatal(self, task, message):
        self.__write(logging.FATAL, task, message)

    def error(self, task, message):
        self.__write(logging.ERROR, task, message)

    def warning(self, task, message):
        self.__write(logging.WARNING, task, message)

    def info(self, task, message):
        self.__write(logging.INFO, task, message)

    def debug(self, task, message):
        self.__write(logging.DEBUG, task, message)

    def __write(self, level, task, message):
        self.logger.log(level, '[{}] {} (url: {})'.format(task.name, message, task.url))
