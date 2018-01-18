# parser_extender.py
# Common parser functions (like check custom errors, count stat, etc)
# r3

import logging
import traceback
import types

from grab.spider import Task

from d_parser.helpers.logger_overrider import Log
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator

logger = logging.getLogger('ddd_site_parse')


def extend_class(self, new_methods):
    for method in new_methods:
        if type(method) is types.FunctionType and not getattr(self, method.__name__, None):
            setattr(self, method.__name__, method)


def get_body(grab):
    return grab.doc.unicode_body()


def check_errors(self, task):
    if task.task_try_count < self.err_limit:
        self.log.error(task, 'Restart task, attempt {}'.format(task.task_try_count))
        return Task(
            task.name,
            url=task.url,
            priority=task.priority + 5,
            task_try_count=task.task_try_count + 1,
            raw=True)

    err = 'Skip task, attempt {}'.format(task.task_try_count)
    self.log.error(task, err)
    raise Exception(err)


def check_body_errors(self, grab, task):
    self.log.info(task, 'Start'.format(task.url))

    try:
        self.status_counter[str(grab.doc.code)] += 1

    except KeyError:
        self.status_counter[str(grab.doc.code)] = 1

    if grab.doc.body == '' or grab.doc.code != 200:
        err = '[{}] Code is {}, url is {}, body is {}'.format(task.name, grab.doc.code, task.url, grab.doc.body)
        self.log.error(task, err)
        return True

    return False


def process_error(self, grab, task, exception):
    try:
        self.status_counter['EXC'] += 1

    except KeyError:
        self.status_counter['EXC'] = 1

    if Config.get('APP_LOG_HTML_ERR', '') == 'True':
        html = get_body(grab)
    else:
        html = '(skipped by config)'

    self.log.error(task, 'Parse failed ({}: {})\nTraceback: {}\nDebug HTML: {}'
                   .format(type(exception).__name__, exception, traceback.format_exc(), html))


def process_finally(self, task):
    self.log.info(task, 'Finish')


def common_init(self, try_limit):
    Ree.init()

    self.result = []
    self.status_counter = {}
    self.cookie_jar = {}

    self.domain = UrlGenerator.get_host_from_url(Config.get_seq('SITE_URL')[0])
    self.err_limit = try_limit

    self.log = Log(logger)
    self.logger = logger
    self.logger.info('Init parser ok...')
