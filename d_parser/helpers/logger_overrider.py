import logging

from grab.spider import Task


class Log:
    def __init__(self, logger):
        self.logger = logger

    def critical(self, message: str, task: Task = None) -> None:
        self.__write(logging.CRITICAL, message, task)

    def fatal(self, message: str, task: Task = None) -> None:
        self.__write(logging.FATAL, message, task)

    def error(self, message: str, task: Task = None) -> None:
        self.__write(logging.ERROR, message, task)

    def warning(self, message: str, task: Task = None) -> None:
        self.__write(logging.WARNING, message, task)

    def info(self, message: str, task: Task = None) -> None:
        self.__write(logging.INFO, message, task)

    def debug(self, message: str, task: Task = None) -> None:
        self.__write(logging.DEBUG, message, task)

    def __write(self, level, message: str, task: Task) -> None:
        if not task:
            self.logger.log(level, f'[...] {message}')
            return

        self.logger.log(level, f'[{task.name}] {message} (url: {task.url})')
