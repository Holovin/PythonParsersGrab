import logging
import traceback

from grab.spider import Spider, Task

from d_parser.helpers.logger_overrider import Log
from d_parser.helpers.re_set import Ree
from d_parser.helpers.stat_counter import StatCounter
from helpers.config import Config
from helpers.url_generator import UrlGenerator


class DSpiderCommon(Spider):
    initial_urls = Config.get_seq('SITE_URL')
    logger = logging.getLogger('ddd_site_parse')

    # GRAB
    def __init__(self, thread_number: int, try_limit: int = 0) -> None:
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')

        # Logger
        self.log = Log(DSpiderCommon.logger)
        self.logger = DSpiderCommon.logger

        # Re module init
        Ree.init()

        # Work data
        self.single_task_mode = False
        self.tasks_store = {}
        self.result = []
        self.cookie_jar = {}

        # Info
        self.info = StatCounter()
        self.info.add_task(StatCounter.TASK_FACTORY)

        # Common vars
        self.domain = UrlGenerator.get_host_from_url(Config.get_seq('SITE_URL')[0])
        self.err_limit = try_limit

        # Cache
        cache_enabled = Config.get('APP_CACHE_ENABLED', '')
        cache_db_host = Config.get('APP_CACHE_DB_HOST', '')

        if cache_enabled and cache_db_host:
            cache_db_name = Config.get('APP_CACHE_DB_NAME', 'pythonparsers')
            cache_db_type = Config.get('APP_CACHE_DB_TYPE', 'mysql')
            cache_db_port = int(Config.get('APP_CACHE_DB_PORT', '3306'))
            cache_db_user = Config.get('APP_CACHE_DB_USER', 'root')
            cache_db_pass = Config.get('APP_CACHE_DB_PASS', '')

            if cache_db_user and cache_db_pass:
                self.setup_cache(backend=cache_db_type, database=cache_db_name, host=cache_db_host, port=cache_db_port, user=cache_db_user, password=cache_db_pass)
            else:
                self.setup_cache(backend=cache_db_type, database=cache_db_name, host=cache_db_host, port=cache_db_port)

            self.logger.info('!!! CACHE MODE ENABLED !!!')

        # Debug mode (only 1 iteration of each task)
        if Config.get('APP_SINGLE_TASK', ''):
            self.logger.info('!!! SINGLE MODE ENABLED !!!')
            self.single_task_mode = True

        self.logger.info('Init parser ok...')

    def create_grab_instance(self, **kwargs):
        grab = super(DSpiderCommon, self).create_grab_instance(**kwargs)

        # setup cookies
        if self.cookie_jar:
            grab.cookies.cookiejar = self.cookie_jar

        cookies = Config.get_dict('APP_COOKIE_NAME', 'APP_COOKIE_VALUE', default_value={})
        grab.setup(cookies=cookies)

        return grab

    def task_initial(self, grab, task):
        try:
            pass
            # override base task when we use task_generator instead initial

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # EXTEND
    def do_task(self, name, url, priority, task_try_count=0, last=False, raw=True):
        if self.single_task_mode:
            if self.tasks_store.get(name, ''):
                return
            else:
                self.tasks_store[name] = 'done'

        if last:
            self.info.add_task()
        else:
            self.info.add_task(StatCounter.TASK_FACTORY)

        return Task(name, url=url, priority=priority, task_try_count=task_try_count, raw=raw)

    def task_noop(self):
        return

    def get_body(self, grab):
        return grab.doc.unicode_body()

    def check_body_errors(self, grab, task):
        self.log.info('Start', task)
        self.info.add(grab.doc.code)

        if grab.doc.body == '' or grab.doc.code != 200:
            err = f'Code is {grab.doc.code}, url is {task.url}, body is {grab.doc.body}'
            self.log.error(err, task)
            return True

        return False

    def check_errors(self, task, last=False):
        if task.task_try_count < self.err_limit:
            self.log.error(f'Restart task, attempt {task.task_try_count}', task)
            return self.do_task(task.name, task.url, task.priority + 5, task.task_try_count + 1, last)

        err = f'Skip task, attempt {task.task_try_count}'
        self.log.error(err, task)
        raise Exception(err)

    def process_error(self, grab, task, exception):
        self.info.add(type(exception).__name__)

        if Config.get('APP_LOG_HTML_ERR', '') == 'True':
            html = self.get_body(grab)
        else:
            html = '(html source - skipped by config)'

        self.log.error(f'Parse failed ({type(exception).__name__}: {exception})'
                       f'\nTraceback: {traceback.format_exc()}'
                       f'\nDebug HTML: {html}', task)

    def process_finally(self, task, last=False):
        if last:
            self.info.done_task()
        else:
            self.info.done_task(StatCounter.TASK_FACTORY)

        self.log.info(f'[{self.info.get_tasks(StatCounter.TASK_TOTAL)}, '
                      f'{self.info.get_tasks(StatCounter.TASK_FACTORY)}, '
                      f'{self.info.get_tasks(StatCounter.TASK_TOTAL_NO_DROP)}] '
                      f'Finish...', task)

    def get_stats(self):
        return self.info.process_stats()
