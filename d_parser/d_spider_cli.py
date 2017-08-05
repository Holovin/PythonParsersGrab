import logging
import urllib.parse

from grab.spider import Spider, Task

from helpers.config import Config
from helpers.output import Output
from helpers.url_generator import UrlGenerator
from d_parser.extend.check_body_errors import check_body_errors
from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.get_body import get_body
from d_parser.helpers.re_set import Ree


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')

    def __init__(self, thread_number, logger_name, writer, try_limit=0):
        DSpider._check_body_errors = check_body_errors

        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')

        self.logger = logging.getLogger(logger_name)
        self.result = writer
        self.status_counter = {}
        self.cookie_jar = {}
        self.err_limit = try_limit
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(Config.get_seq('SITE_URL')[0]))
        self.logger.info('Init parser ok...')

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)

        return cookies_init(self.cookie_jar, g)

    def task_initial(self, grab, task):
        self.logger.debug('[items] Parse page: {}'.format(task.url))

        try:
            if self._check_body_errors(task, grab.doc, '[items]'):
                if task.task_try_count < self.err_limit:
                    self.logger.error('[items] Restart task with url {}, attempt {}'.format(task.url, task.task_try_count))
                    yield Task('parse_items', url=task.url, priority=110, task_try_count=task.task_try_count + 1,
                               raw=True)
                else:
                    self.logger.error('[items] Skip task with url {}, attempt {}'.format(task.url, task.task_try_count))

                return

            table_wrapper = grab.doc.select('//div[contains(@class, "table-wrapper")]')

            # UNIT (global for all page)
            unit = table_wrapper.select('./table/thead//th[5]').text().split(', ')[1].strip()

            rows = table_wrapper.select('./table/tbody/tr')

            for index, row in enumerate(rows):
                # COUNT
                # replace all spaces, because count can be like '1 111' when its = 1111
                count = row.select('./td[5]').text().replace(' ', '')

                # skip if count is wrong [need here?]
                if not Ree.number.match(count):
                    self.logger.warning('[items] Text {} is not a number, skip (url: {})'.format(count, task.url))
                    continue

                # PRICE
                price_raw = row.select('./td[6]').text().strip()
                match = Ree.price_extractor.match(price_raw)
                # check & fix
                if not match:
                    self.logger.warning('[items] Skip item, because price is {} (line: {})'.format(price_raw, index))
                    continue

                price = match.groupdict()['price'].replace(',', '.')

                # NAME
                item_name = row.select('./td[2]').text().strip()

                # OUTPUT
                self.logger.debug('[items] Item added, index {} at url {}'.format(index, task.url))
                self.result.writerow([item_name, count, unit, price])

        except Exception as e:
            html = get_body(grab)
            err = '[items] Url {} parse failed (e: {}), debug: {}'.format(task.url, e, '')
            # Output.print(err)
            self.logger.error(err)
