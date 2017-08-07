import logging
import urllib.parse

from grab.spider import Spider, Task

from d_parser.helpers import url_lib
from d_parser.helpers.el_parser import get_max_page
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
        self.domain = url_lib.get_host_from_url(Config.get_seq('SITE_URL')[0])
        self.logger.info('Init parser ok...')

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, g)

    def task_initial(self, grab, task):
        max_page = 0

        if self._check_body_errors(task, grab.doc, '[start]'):
            err = '[start] Err task with url {}, attempt {}'.format(task.url, task.task_try_count)
            self.logger.fatal(err)
            return

        items = grab.doc.select('//div[@class="catalog-pagenav"]//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM')))
        max_page = get_max_page(items)

        self.logger.info('[prep] Task: {}, max_page: {}'.format(task.url, max_page))

        url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))

        for p in range(1, max_page + 1):
            url = url_gen.get_page(p)
            yield Task('parse_page', url=url, priority=90)

        self.logger.info('[prep] Tasks added...')

    def task_parse_page(self, grab, task):
        self.logger.debug('[items] Parse page: {}'.format(task.url))

        try:
            if self._check_body_errors(task, grab.doc, '[items]'):
                if task.task_try_count < self.err_limit:
                    self.logger.error('[items] Restart task with url {}, attempt {}'.format(task.url, task.task_try_count))
                    yield Task('parse_items', url=task.url, priority=110, task_try_count=task.task_try_count + 1, raw=True)
                else:
                    self.logger.error('[items] Skip task with url {}, attempt {}'.format(task.url, task.task_try_count))

                return

            table = grab.doc.select('//div[@class="catalog-section-it-table"]')

            # UNIT (global for all page)
            unit = table.select('.//div[@class="catalog_quantity"]').text().split(', ')[1].strip()

            rows = table.select('.//div[contains(@class, "catalog-section-it-row")]')

            for index, row in enumerate(rows):
                # COUNT
                count = row.select('./div[contains(@class, "catalog_quantity")]').text().strip()

                # skip if count is wrong
                if count == 'Ожидаетсяпоставка' or not Ree.number.match(count):
                    self.logger.warning('[items] Text {} is not a number, skip (url: {})'.format(count, task.url))
                    continue

                # PRICE
                price = Config.get('APP_PRICE_ON_REQUEST')
                # price = row.select('.//td[3]/b/span').text().strip()
                # # check regex
                # price_re_result = Ree.price.match(price)
                # if (not price_re_result or (price_re_result and float(price) < 0)) and price != 'по запросу':
                #     self.logger.warning('[items] Skip item, because price is {} (line: {})'
                #                         .format(price, index, ))
                #     continue
                # # replace
                # if price == 'по запросу':

                # NAME
                item_name = row.select('./div[@class="name"]').text().strip()

                # Debug: go for all inner pages and try find price
                # link = row.select('./div[@class="name"]/a').attr('href')
                # yield Task('parse_items', url=urllib.parse.urljoin(self.domain, link), priority=100, raw=True)

                # OUTPUT
                self.logger.debug('[items] Item added, index {} at url {}'.format(index, task.url))
                self.result.writerow([item_name, count, unit, price])

        except Exception as e:
            html = get_body(grab)
            err = '[items] Url {} parse failed (e: {}), debug: {}'.format(task.url, e, html)
            Output.print(err)
            self.logger.error(err)

    # def task_parse_items(self, grab, task):
    #     if 'Узнать цену' not in get_body(grab):
    #         print(task.url)
