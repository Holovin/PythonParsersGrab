import logging
import traceback

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.logger_overrider import Log
from d_parser.helpers.re_set import Ree
from d_parser.helpers.stat_counter import StatCounter
from helpers.config import Config
from helpers.url_generator import UrlGenerator


class DSpiderCommon(Spider):
    initial_urls = Config.get_seq('SITE_URL')
    logger = logging.getLogger('ddd_site_parse')

    # GRAB
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')

        Ree.init()

        self.result = []
        self.cookie_jar = {}

        self.info = StatCounter()
        self.info.add_task(StatCounter.TASK_FACTORY)

        self.domain = UrlGenerator.get_host_from_url(Config.get_seq('SITE_URL')[0])
        self.err_limit = try_limit

        self.log = Log(DSpiderCommon.logger)
        self.logger = DSpiderCommon.logger
        self.logger.info('Init parser ok...')

    def create_grab_instance(self, **kwargs):
        grab = super(DSpiderCommon, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, grab)

    # EXTEND
    def do_task(self, name, url, priority, task_try_count=0, last=False, raw=True):
        if last:
            self.info.add_task()
        else:
            self.info.add_task(StatCounter.TASK_FACTORY)

        return Task(name, url=url, priority=priority, task_try_count=task_try_count, raw=raw)

    def get_body(self, grab):
        return grab.doc.unicode_body()

    def check_body_errors(self, grab, task):
        self.log.info(task, 'Start'.format(task.url))
        self.info.add(grab.doc.code)

        if grab.doc.body == '' or grab.doc.code != 200:
            err = f'Code is {grab.doc.code}, url is {task.url}, body is {grab.doc.body}'
            self.log.error(task, err)
            return True

        return False

    def check_errors(self, task, last=False):
        if task.task_try_count < self.err_limit:
            self.log.error(task, f'Restart task, attempt {task.task_try_count}')
            return self.do_task(task.name, task.url, task.priority + 5, task.task_try_count + 1, last)

        err = f'Skip task, attempt {task.task_try_count}'
        self.log.error(task, err)
        raise Exception(err)

    def process_error(self, grab, task, exception):
        self.info.add(type(exception).__name__)

        if Config.get('APP_LOG_HTML_ERR', '') == 'True':
            html = self.get_body(grab)
        else:
            html = '(html source - skipped by config)'

        self.log.error(task, f'Parse failed ({type(exception).__name__}: {exception})'
                             f'\nTraceback: {traceback.format_exc()}'
                             f'\nDebug HTML: {html}')

    def process_finally(self, task, last=False):
        if last:
            self.info.done_task()
        else:
            self.info.done_task(StatCounter.TASK_FACTORY)

        self.log.info(task, f'[{self.info.get_tasks(StatCounter.TASK_TOTAL)}, '
                            f'{self.info.get_tasks(StatCounter.TASK_FACTORY)}, '
                            f'{self.info.get_tasks(StatCounter.TASK_TOTAL_NO_DROP)}] '
                            f'Finish...')

    def get_stats(self):
        return self.info.process_stats()
