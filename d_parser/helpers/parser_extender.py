# parser_extender.py
# Common parser functions (like check custom errors, count stat, etc)
# r2

import logging
import traceback
import types

from grab.spider import Task
from grab.spider.task import BaseTask

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
        self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
        return Task(
            task.name,
            url=task.url,
            priority=task.priority + 5,
            task_try_count=task.task_try_count + 1,
            raw=True)

    err = '[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count)
    self.logger.error(err)
    raise Exception(err)


def check_body_errors(self, grab, task):
    self.logger.info('[{}] Start: {}'.format(task.name, task.url))

    try:
        self.status_counter[str(grab.doc.code)] += 1

    except KeyError:
        self.status_counter[str(grab.doc.code)] = 1

    if grab.doc.body == '' or grab.doc.code != 200:
        err = '[{}] Code is {}, url is {}, body is {}'.format(task.name, grab.doc.code, task.url, grab.doc.body)
        self.logger.error(err)
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

    self.logger.error('[{}] Url {} parse failed ({}: {})'
                      '\nTraceback: {}'
                      '\nDebug HTML: {}'.format(task.name, task.url, type(exception).__name__, exception, traceback.format_exc(), html))


def process_finally(self, task):
    self.logger.info('[{}] Finish: {}'.format(task.name, task.url))


def common_init(self, try_limit):
    Ree.init()

    self.result = []
    self.logger = logger
    self.status_counter = {}
    self.cookie_jar = {}
    self.err_limit = try_limit
    self.domain = UrlGenerator.get_host_from_url(Config.get_seq('SITE_URL')[0])
    self.logger.info('Init parser ok...')
