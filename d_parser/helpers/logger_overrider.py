import logging

from grab.spider import Task


class Log:
    def __init__(self, logger):
        self.logger = logger

    def critical(self, task: Task, message: str) -> None:
        self.__write(logging.CRITICAL, task, message)

    def fatal(self, task: Task, message: str) -> None:
        self.__write(logging.FATAL, task, message)

    def error(self, task: Task, message: str) -> None:
        self.__write(logging.ERROR, task, message)

    def warning(self, task: Task, message: str) -> None:
        self.__write(logging.WARNING, task, message)

    def info(self, task: Task, message: str) -> None:
        self.__write(logging.INFO, task, message)

    def debug(self, task: Task, message: str) -> None:
        self.__write(logging.DEBUG, task, message)

    def __write(self, level, task: Task, message: str) -> None:
        self.logger.log(level, '[{}] {} (url: {})'.format(task.name, message, task.url))
