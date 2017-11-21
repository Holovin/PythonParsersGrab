import urllib.parse

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.el_parser import get_max_page
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator


# Don't remove task argument even if not use it (it's break grab and spider crashed)
# noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')

    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')
        DSpider._check_body_errors = check_body_errors
        DSpider._process_error = process_error
        DSpider._common_init = common_init
        self._common_init(try_limit)

        Ree.init()
        Ree.is_page_number(Config.get('SITE_PAGE_PARAM'))

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, g)

    def task_initial(self, grab, task):
        self.logger.debug('[{}] Initial url: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[{}] Err task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
            return

        try:
            items = grab.doc.select('//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM')))
            max_page = get_max_page(items, 1, 1)

            url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))

            for p in range(1, max_page + 1):
                url = url_gen.get_page(p)
                yield Task('parse_page', url=url, priority=90)

            self.logger.info('[{}] Tasks added...'.format(task.name))

        except Exception as e:
            self._process_error(grab, task, e)

    def task_parse_page(self, grab, task):
        self.logger.debug('[{}] Parse page: {}'.format(task.name, task.url))

        try:
            if self._check_body_errors(grab, task):
                if task.task_try_count < self.err_limit:
                    self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                    yield Task('parse_page', url=task.url, priority=105, task_try_count=task.task_try_count + 1, raw=True)
                else:
                    self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))

                return

            rows = grab.doc.select('//div[@class="products"]/table[@class="prod"]//tr[not(contains(@class, "white"))]')

            for index, row in enumerate(rows):
                # COUNT
                count = row.select('./td[2]').text().strip()
                # skip useless tasks
                if count == '0':
                    self.logger.debug('[{}] Skip at {} (line: {}), not in store ({})'.format(task.name, task.url, index, count))
                    continue

                # PRICE
                price = row.select('./td[@class="pr"]').text().replace('от ', '', 1).replace(' .', '', 1).replace(',', '', 1).strip()

                # skip useless tasks
                if price == 'под заказ':
                    self.logger.debug('[{}] Skip at {} (line: {}), not available ({})'.format(task.name, task.url, index, price))
                    continue

                # check regex
                if not Ree.float.match(price):
                    self.logger.warning('[{}] Skip at {} (line: {}), not valid price format {}'.format(task.name, task.url, index, price))
                    continue

                # check less zero
                if float(price) <= 0:
                    self.logger.warning('[{}] Skip at {} (line: {}), price invalid {}'.format(task.name, task.url, index, price))
                    continue

                # URL
                url = row.select('./td[@class="name"]/a').attr('href')
                url = urllib.parse.urljoin(self.domain, url)
                self.logger.debug('[{}] Add page: {}'.format(task.name, url))

                yield Task('parse_items', url=url, priority=100, raw=True)

        except Exception as e:
            self.logger.error('[{}] Url {} parse failed (e: {})'.format(task.name, task.url, e))

    def task_parse_items(self, grab, task):
        self.logger.debug('[{}] Parse page: {}'.format(task.name, task.url))

        try:
            if self._check_body_errors(grab, task):
                if task.task_try_count < self.err_limit:
                    self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                    yield Task('parse_items', url=task.url, priority=110, task_try_count=task.task_try_count + 1, raw=True)

                else:
                    self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))

                return

            rows = grab.doc.select('//div[@id="primary_block"]//table[@class="prod"]//tr[contains(@class, "product")]')

            for index, row in enumerate(rows):
                # COUNT
                count = row.select('./td[@class="st"]').text().strip()
                # skip if count is not a number
                if not Ree.number.match(count):
                    self.logger.warning('[{}] Text {} is not a number, skip (url: {})'.format(task.name, count, task.url))
                    continue
                # skip if count less zero
                if int(count) < 1:
                    self.logger.warning('[{}] Number {} is less than zero, skip (url: {})'.format(task.name, count, task.url))
                    continue

                # PRICE
                price = row.select('./td[@class="pr"]').text().replace(' .', '', 1).replace(',', '', 1).strip()
                # check regex
                if not Ree.float.match(price):
                    self.logger.warning('[{}] Skip item, because price is {} (line: {})'.format(task.name, price, index))
                    continue

                # skip if zero
                if float(price) <= 0:
                    self.logger.warning('[{}] Price {} is less than zero, skip (url: {})'.format(task.name, price, task.url))
                    continue

                # UNIT
                unit = row.select('./td[@class="but"]/form[@class="variants"]//tr/td[2]').text().strip()
                # use default value
                if unit == '':
                    unit = 'ед.'

                # NAME
                item_name = row.select('./td[@class="name"]').text().strip()

                # OUTPUT
                self.logger.debug('[{}] Item added, index {} at url {}'.format(task.name, index, task.url))
                self.result.append({
                    'name': item_name,
                    'count': count,
                    'unit': unit,
                    'price': price
                })

        except Exception as e:
            self._process_error(grab, task, e)
