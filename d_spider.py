import logging
import re
import urllib.parse

from grab.spider import Spider, Task

from config.config import Config
from helpers.url_generator import UrlGenerator


# Don't remove task argument even if not use it (it's break grab and spider crashed)
# noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(Config.get_seq('SITE_URL')[0]))

    re_page_number = re.compile('{}=(\d+)'.format(Config.get('SITE_PAGE_PARAM')))
    re_count = re.compile('^\d+$')
    re_price = re.compile('^\d+(.\d+)?$')

    def __init__(self, thread_number, logger_name, writer, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')
        self.logger = logging.getLogger(logger_name)
        self.result = writer
        self.logger.info('Init parser ok...')

    def task_initial(self, grab, task):
        max_page = 0

        for page_link in grab.doc.select('//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM'))):
            match = self.re_page_number.search(page_link.attr('href'))

            if len(match.groups()) == 1:
                page_number = match.group(1)
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
                raise Exception(err)

        self.logger.info('[prep] Task: {}, max_page: {}'.format(task.url, max_page))

        url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))

        for p in range(1, max_page + 1):
            url = url_gen.get_page(p)
            yield Task('parse_page', url=url, priority=90)

        self.logger.info('[prep] Tasks added...')

    def task_parse_page(self, grab, task):
        self.logger.info('[page] Find tasks: {}'.format(task.url))
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
            price = row.select('./td[@class="pr"]').text()\
                .replace('от ', '', 1)\
                .replace(' .', '', 1)\
                .replace(',', '', 1).\
                strip()

            # skip useless tasks
            if price == 'под заказ':
                self.logger.debug('[page] Skip at {} (line: {}), not available ({})'
                                  .format(task.url, index, price))
                continue

            # check regex
            if not self.re_price.match(price):
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

            yield Task('parse_items', url=url, priority=100)

    def task_parse_items(self, grab, task):
        self.logger.debug('[items] Parse page: {}'.format(task.url))

        try:
            rows = grab.doc.select('//div[@id="primary_block"]//table[@class="prod"]//tr[contains(@class, "product")]')
            for index, row in enumerate(rows):
                # COUNT
                count = row.select('./td[@class="st"]').text().strip()
                # skip if count is number
                if not self.re_count.match(count):
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
                if not self.re_price.match(price):
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
                output_line = '{} {} {} {}'.format(item_name, count, unit, price)
                self.result.writerow([item_name, count, unit, price])

        except Exception as e:
            err = 'Url {} parse failed (e: {})'.format(task.url, e)
            print(err)
            self.logger.error(err)
            yield Task('parse_items', url=task.url, task_try_count=task.task_try_count + 1)

    def task_parse_page_fallback(self, task):
        self._go_err(task)

    def task_parse_items_fallback(self, task):
        self._go_err(task)

    def _go_err(self, task):
        err = 'Url {} request failed! Try less APP_THREAD_COUNT!'.format(task.url)
        self.logger.fatal(err)
        print(err)