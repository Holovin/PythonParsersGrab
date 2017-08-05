import logging
import urllib.parse

from grab import Grab
from grab.spider import Spider, Task

from helpers.config import Config
from helpers.output import Output
from helpers.url_generator import UrlGenerator
from d_parser.extend.check_body_errors import check_body_errors
from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.re_set import Ree


# Don't remove task argument even if not use it (it's break grab and spider crashed)
# noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(Config.get_seq('SITE_URL')[0]))

    def __init__(self, thread_number, logger_name, writer, try_limit=0):
        DSpider._check_body_errors = check_body_errors

        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')

        self.logger = logging.getLogger(logger_name)
        self.result = writer
        self.status_counter = {}
        self.cookie_jar = None
        self.err_limit = try_limit
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(Config.get_seq('SITE_URL')[0]))
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

        for page_link in grab.doc.select('//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM'))):
            match = Ree.page_number.search(page_link.attr('href'))

            if match:
                page_number = match.groupdict()['page']
                self.logger.debug('[prep] Find max_page: {}'.format(page_number))

                int_page_number = int(page_number)

                if int_page_number > max_page:
                    self.logger.debug('[prep] Set new max_page: {} => {}'.format(max_page, page_number))
                    max_page = int_page_number

        else:
            self.logger.debug('[prep] Max page is: {}'.format(max_page))

            if max_page < 1:
                err = '[prep] Bad page counter: {}'.format(max_page)
                self.logger.error(err)
                Output.print(err)

                raise Exception(err)

        self.logger.info('[prep] Task: {}, max_page: {}'.format(task.url, max_page))

        url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))

        for p in range(1, max_page + 1):
            url = url_gen.get_page(p)
            yield Task('parse_page', url=url, priority=90)

        self.logger.info('[prep] Tasks added...')

    def task_parse_page(self, grab, task):
        self.logger.info('[page] Find tasks: {}'.format(task.url))

        try:
            if self._check_body_errors(task, grab.doc, '[page]'):
                if task.task_try_count < self.err_limit:
                    self.logger.error(
                        '[page] Restart task with url {}, attempt {}'.format(task.url, task.task_try_count))
                    yield Task('parse_page', url=task.url, priority=110, task_try_count=task.task_try_count + 1,
                               raw=True)
                else:
                    self.logger.error(
                        '[page] Skip task with url {}, attempt {}'.format(task.url, task.task_try_count))

                return

            rows = grab.doc.select('//div[@class="products"]/table[@class="prod"]//tr[not(contains(@class, "white"))]')

            for index, row in enumerate(rows):
                # COUNT
                count = row.select('./td[2]').text().strip()
                # skip useless tasks
                if count == '0':
                    self.logger.debug('[page] Skip at {} (line: {}), not in store ({})'
                                      .format(task.url, index, count))
                    continue

                # PRICE
                price = row.select('./td[@class="pr"]').text() \
                    .replace('от ', '', 1) \
                    .replace(' .', '', 1) \
                    .replace(',', '', 1). \
                    strip()

                # skip useless tasks
                if price == 'под заказ':
                    self.logger.debug('[page] Skip at {} (line: {}), not available ({})'
                                      .format(task.url, index, price))
                    continue

                # check regex
                if not Ree.price.match(price):
                    self.logger.warning('[page] Skip at {} (line: {}), not valid price format {}'
                                        .format(task.url, index, price))
                    continue

                # check less zero
                if float(price) <= 0:
                    self.logger.warning('[page] Skip at {} (line: {}), price invalid {}'
                                        .format(task.url, index, price))
                    continue

                # URL
                url = row.select('./td[@class="name"]/a').attr('href')
                url = urllib.parse.urljoin(self.domain, url)
                self.logger.debug('[page] Add page: {}'.format(url))

                yield Task('parse_items', url=url, priority=100, raw=True)

        except Exception as e:
            err = '[page] Url {} parse failed (e: {})'.format(task.url, e)
            Output.print(err)
            self.logger.error(err)

    def task_parse_items(self, grab, task):
        self.logger.debug('[items] Parse page: {}'.format(task.url))

        try:
            if self._check_body_errors(task, grab.doc, '[items]'):
                if task.task_try_count < self.err_limit:
                    self.logger.error(
                        '[items] Restart task with url {}, attempt {}'.format(task.url, task.task_try_count))
                    yield Task('parse_items', url=task.url, priority=110, task_try_count=task.task_try_count + 1,
                               raw=True)
                else:
                    self.logger.error(
                        '[items] Skip task with url {}, attempt {}'.format(task.url, task.task_try_count))

                return

            rows = grab.doc.select('//div[@id="primary_block"]//table[@class="prod"]//tr[contains(@class, "product")]')

            for index, row in enumerate(rows):
                # COUNT
                count = row.select('./td[@class="st"]').text().strip()
                # skip if count is not a number
                if not Ree.number.match(count):
                    self.logger.warning('[items] Text {} is not a number, skip (url: {})'
                                        .format(count, task.url))
                    continue
                # skip if count less zero
                if int(count) < 1:
                    self.logger.warning('[items] Number {} is less than zero, skip (url: {})'
                                        .format(count, task.url))
                    continue

                # PRICE
                price = row.select('./td[@class="pr"]').text()\
                    .replace(' .', '', 1)\
                    .replace(',', '', 1)\
                    .strip()
                # check regex
                if not Ree.price.match(price):
                    self.logger.warning('[items] Skip item, because price is {} (line: {})'
                                        .format(price, index, ))
                    continue

                # skip if zero
                if float(price) <= 0:
                    self.logger.warning('[items] Price {} is less than zero, skip (url: {})'
                                        .format(price, task.url))
                    continue

                # UNIT
                unit = row.select('./td[@class="but"]/form[@class="variants"]//tr/td[2]').text().strip()
                # use default value
                if unit == '':
                    unit = 'ед.'

                # NAME
                item_name = row.select('./td[@class="name"]').text().strip()

                # OUTPUT
                self.logger.debug('[items] Item added, index {} at url {}'.format(index, task.url))
                self.result.writerow([item_name, count, unit, price])

        except Exception as e:
            err = '[items] Url {} parse failed (e: {}), debug: {}'.format(task.url, e, grab.doc.text())
            Output.print(err)
            self.logger.error(err)
