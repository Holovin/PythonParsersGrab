import logging
import urllib.parse

from grab import Grab
from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.el_parser import get_max_page
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')

    def __init__(self, thread_number, writer, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')
        DSpider._check_body_errors = check_body_errors
        DSpider._process_error = process_error
        DSpider._common_init = common_init
        self._common_init(writer, try_limit)

        Ree.init()
        Ree.is_page_number(Config.get('SITE_PAGE_PARAM'))

    def prepare(self):
        g = Grab()
        g.go(Config.get_seq('SITE_URL')[0])

        url = urllib.parse.urljoin(self.domain, '/udata/content/setSortParams/name/ascending')
        g.setup(post={})
        g.go(url)

        self.cookie_jar = g.cookies.cookiejar

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, g)

    def task_initial(self, grab, task):
        self.logger.debug('[{}] Initial url: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[start] Err task with url {}, attempt {}'.format(task.url, task.task_try_count))
            return

        try:
            items = grab.doc.select('//div[contains(@class, "pagination")]//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM')))
            max_page = get_max_page(items, 0, -1)

            self.logger.info('[{}] Task: {}, max_page: {}'.format(task.name, task.url, max_page))

            url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))

            for p in range(0, max_page + 1):
                url = url_gen.get_page(p)
                yield Task('parse_page', url=url, priority=90)

        except Exception as e:
            self._process_error(grab, task, e)

        self.logger.info('[{}] Tasks added...'.format(task.name))

    def task_parse_page(self, grab, task):
        self.logger.debug('[{}] Parse page: {}'.format(task.name, task.url))

        try:
            if self._check_body_errors(grab, task):
                if task.task_try_count < self.err_limit:
                    self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                    yield Task('parse_items', url=task.url, priority=110, task_try_count=task.task_try_count + 1, raw=True)
                else:
                    self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                return

            rows = grab.doc.select('//div[@class="products-wrap"]//table[contains(@class, "products")]')

            for index, row in enumerate(rows):
                # COUNT
                count = row.select('.//td[5]/span').text().strip()
                # skip if count is wrong
                if count == 'под заказ':
                    self.logger.debug('[{}] Text {} is not a number, skip (url: {})'.format(task.name, count, task.url))
                    continue

                # PRICE
                price = row.select('.//td[3]/b/span').text().strip()
                # check regex
                price_re_result = Ree.float.match(price)
                if (not price_re_result or (price_re_result and float(price) < 0)) and price != 'по запросу':
                    self.logger.warning('[{}] Skip item, because price is {} (line: {})'.format(task.name, price, index))
                    continue
                # replace
                if price == 'по запросу':
                    price = Config.get('APP_PRICE_ON_REQUEST')

                # UNIT
                count, unit = count.split(' ', maxsplit=1)
                # use default value
                if unit == '':
                    unit = 'ед.'

                # NAME
                item_name = row.select('.//td[2]').text().strip()

                # OUTPUT
                self.logger.debug('[{}] Item added, index {} at url {}'.format(task.name, index, task.url))
                self.result.writerow([item_name, count, unit, price])

        except Exception as e:
            self._process_error(grab, task, e)
