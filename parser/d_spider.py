import logging
import re
import urllib.parse

from grab import Grab
from grab.spider import Spider, Task

from helpers.config import Config
from helpers.output import Output
from helpers.re_set import Ree
from helpers.url_generator import UrlGenerator
from parser.extend_methods import check_body_errors


# Don't remove task argument even if not use it (it's break grab and spider crashed)
# noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urllib.parse.urlparse(Config.get_seq('SITE_URL')[0]))
    err_limit = int(Config.get('APP_TRY_LIMIT'))
    cookie_jar = None

    def __init__(self, thread_number, logger_name, writer, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')

        self.logger = logging.getLogger(logger_name)
        self.result = writer
        self.status_counter = {}

        self.logger.info('Init parser ok...')
        DSpider._check_body_errors = check_body_errors

    def prepare(self):
        g = Grab()
        g.go(Config.get_seq('SITE_URL')[0])

        url = urllib.parse.urljoin(self.domain, '/udata/content/setSortParams/name/ascending')
        g.setup(post={})
        g.go(url)

        self.cookie_jar = g.cookies.cookiejar

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        g.cookies.cookiejar = self.cookie_jar

        cookie_name = Config.get('APP_COOKIE_NAME', '')
        cookie_value = Config.get('APP_COOKIE_VALUE', '')

        if cookie_name != '' and cookie_value != '':
            g.setup(cookies={cookie_name: cookie_value})

        return g

    def task_initial(self, grab, task):
        max_page = 0

        if self._check_body_errors(task, grab.doc, '[start]'):
            err = '[start] Err task with url {}, attempt {}'.format(task.url, task.task_try_count)
            self.logger.fatal(err)
            return

        for page_link in grab.doc.select('//div[contains(@class, "pagination")]//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM'))):
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

        for p in range(0, max_page + 1):
            url = url_gen.get_page(p)
            yield Task('parse_page', url=url, priority=90)

        self.logger.info('[prep] Tasks added...')

    def task_parse_page(self, grab, task):
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

            rows = grab.doc.select('//div[@class="products-wrap"]//table[contains(@class, "products")]')

            for index, row in enumerate(rows):
                # COUNT
                count = row.select('.//td[5]/span').text().strip()
                # skip if count is wrong
                if count == 'под заказ':
                    self.logger.warning('[items] Text {} is not a number, skip (url: {})'
                                        .format(count, task.url))
                    continue

                # PRICE
                price = row.select('.//td[3]/b/span').text().strip()
                # check regex
                price_re_result = Ree.price.match(price)
                if (not price_re_result or (price_re_result and float(price) < 0)) and price != 'по запросу':
                    self.logger.warning('[items] Skip item, because price is {} (line: {})'
                                        .format(price, index, ))
                    continue
                # replace
                if price == 'по запросу':
                    price = Config.get('APP_ON_REQUEST')

                # UNIT
                count, unit = count.split(' ', maxsplit=1)
                # use default value
                if unit == '':
                    unit = 'ед.'

                # NAME
                item_name = row.select('.//td[2]').text().strip()

                # OUTPUT
                self.logger.debug('[items] Item added, index {} at url {}'.format(index, task.url))
                self.result.writerow([item_name, count, unit, price])

        except Exception as e:
            err = '[items] Url {} parse failed (e: {}), debug: {}'.format(task.url, e, grab.doc.text())
            Output.print(err)
            self.logger.error(err)
