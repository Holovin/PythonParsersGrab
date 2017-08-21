import logging

from d_parser.helpers import url_lib
from d_parser.helpers.get_body import get_body
from helpers.config import Config

logger = logging.getLogger('ddd_site_parse')


def check_body_errors(self, grab, task):
    try:
        self.status_counter[str(grab.doc.code)] += 1

    except KeyError:
        self.status_counter[str(grab.doc.code)] = 1

    if grab.doc.body == '' or grab.doc.code != 200:
        err = '[{}] Code is {}, url is {}, body is {}'.format(task.name, grab.doc.code, task.url, grab.doc.body)
        logger.error(err)
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

    self.logger.error('[{}] Url {} parse failed ({}: {}), debug: {}'.format(task.name, task.url, type(exception).__name__, exception, html))


def common_init(self, try_limit):
    self.result = []
    self.logger = logger
    self.status_counter = {}
    self.cookie_jar = {}
    self.err_limit = try_limit
    self.domain = url_lib.get_host_from_url(Config.get_seq('SITE_URL')[0])
    self.logger.info('Init parser ok...')
