import logging
import urllib.parse

from grab.spider import Spider, Task

from helpers.config import Config
from helpers.output import Output
from helpers.url_generator import UrlGenerator
from d_parser.extend.check_body_errors import check_body_errors
from d_parser.helpers.cookies_init import cookies_init_v2
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

        self.const_zero_stock = Config.get('APP_STOCK_ZERO')
        self.const_price_sep = Config.get('APP_PRICE_SEP')
        self.const_enc = Config.get('APP_OUTPUT_ENC')

        self.logger.info('Init parser ok...')

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)

        return cookies_init_v2(self.cookie_jar, g)

    def task_initial(self, grab, task):
        self.logger.debug('[cats] Parse page: {}'.format(task.url))

        try:
            if self._check_body_errors(task, grab.doc, '[items]'):
                self.logger.error('[cats] Skip task with url {}, attempt {}'.format(task.url, task.task_try_count))
                return

            cats = grab.doc.select('//a[contains(@href, "/catalog/")]')
            links = []

            # get cats
            for index, cat in enumerate(cats):
                url = cat.select('.').attr('href')

                if url not in links and url != '/catalog/':
                    url = urllib.parse.urljoin(self.domain, url)
                    links.append(url)

                    yield Task('parse_pre_page', url=url, priority=90)
                    self.logger.debug('[cats] Add page: {}'.format(url))

        except Exception as e:
            html = get_body(grab)
            err = '[cats] Url {} parse failed (e: {}), debug: {}'.format(task.url, e, html)
            Output.print(err)
            self.logger.error(err)

    def task_parse_pre_page(self, grab, task):
        self.logger.debug('[page] Parse pagination: {}'.format(task.url))
        max_page = 1

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
            yield Task('parse_page', url=url, priority=100)

        self.logger.info('[prep] Tasks added...')

    def task_parse_page(self, grab, task):
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

            table = grab.doc.select('//div[@class="ajax-wrapper"]')

            rows = table.select('.//div[@class="one-product"]')

            for index, row in enumerate(rows):
                # PRICE
                price = row.select('./span[@class="price"]').text().replace(self.const_price_sep, '.').replace(' ', '')
                # check regex
                price_re_result = Ree.price_extractor.match(price)
                if not price_re_result or price == '':
                    self.logger.warning('[items] Skip item, because price is {} (line: {})'.format(price, index, ))
                    continue

                # NAME
                item_name = row.select('./a[@class="name"]').text().strip()

                # COUNT
                count = row.select('./span[@class="in-stock"]').text().replace(' ', '')
                # skip if count is wrong
                if not Ree.number.match(count):
                    self.logger.warning('[items] Count {} is not a number, skip (url: {})'.format(count, task.url))
                    continue
                # replace if needed
                if count == '0':
                    count = self.const_zero_stock

                # UNIT
                unit = row.select('./span[@class="measure"]').text().strip()
                # replace
                if unit == '':
                    unit = 'ед.'

                # OUTPUT
                self.logger.debug('[items] Item added, index {} at url {}'.format(index, task.url))
                self.result.writerow([item_name.encode(self.const_enc, 'replace').decode('cp1251'), count, unit, price])

        except Exception as e:
            html = get_body(grab)
            err = '[items] Url {} parse failed 2 (e: {}), debug: {}'.format(task.url, e, html)
            Output.print(err)
            self.logger.error(err)
