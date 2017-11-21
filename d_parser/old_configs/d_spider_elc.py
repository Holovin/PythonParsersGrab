import urllib.parse

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init_v2
from d_parser.helpers.el_parser import get_max_page
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
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

        self.const_zero_stock = Config.get('APP_STOCK_ZERO')
        self.const_price_sep = Config.get('APP_PRICE_SEP')
        self.const_enc = Config.get('APP_OUTPUT_ENC')

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init_v2(self.cookie_jar, g)

    def task_initial(self, grab, task):
        self.logger.debug('[{}] Parse page: {}'.format(task.name, task.url))

        try:
            if self._check_body_errors(grab, task):
                self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                return

            cats = grab.doc.select('//a[contains(@href, "/catalog/")]')
            links = []

            # get cats
            for index, cat in enumerate(cats):
                url = cat.select('.').attr('href')

                if url not in links and url != '/catalog/':
                    url = urllib.parse.urljoin(self.domain, url)
                    links.append(url)

                    self.logger.debug('[{}] Add page: {}'.format(task.name, url))
                    yield Task('parse_pre_page', url=url, priority=90)

        except Exception as e:
            self._process_error(grab, task, e)

    def task_parse_pre_page(self, grab, task):
        self.logger.debug('[{}] Parse pagination: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[start] Err task with url {}, attempt {}'.format(task.url, task.task_try_count))
            return

        try:
            items = grab.doc.select('//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM')))
            max_page = get_max_page(items, 1, 1)

            url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))

            for p in range(1, max_page + 1):
                url = url_gen.get_page(p)
                yield Task('parse_page', url=url, priority=100)

            self.logger.info('[{}] Tasks added...'.format(task.name))

        except Exception as e:
            self._process_error(grab, task, e)

    def task_parse_page(self, grab, task):
        self.logger.debug('[{}] Parse page: {}'.format(task.name, task.url))

        try:
            if self._check_body_errors(grab, task):
                if task.task_try_count < self.err_limit:
                    self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                    yield Task('parse_page', url=task.url, priority=110, task_try_count=task.task_try_count + 1, raw=True)
                else:
                    self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))

                return

            table = grab.doc.select('//div[@class="ajax-wrapper"]')

            rows = table.select('.//div[@class="one-product"]')

            for index, row in enumerate(rows):
                # PRICE
                price = row.select('./span[@class="price"]').text().replace(self.const_price_sep, '.').replace(' ', '')
                # check regex
                price_re_result = Ree.float.match(price)
                if price == '':
                    self.logger.debug('[{}] Skip item, because price is {} (line: {})'.format(task.name, price, index))
                    continue
                if not price_re_result:
                    self.logger.warning('[{}] Skip item, because price is {} (line: {})'.format(task.name, price, index))
                    continue

                # NAME
                item_name_a_raw = row.select('./a[@class="name"]')
                item_name_raw = item_name_a_raw.select('./span')
                # item_name_class = item_name_raw.attr('class', None)
                item_name = item_name_raw.text().strip()

                # COUNT
                count = row.select('./span[@class="in-stock"]').text().replace(' ', '')
                # skip if count is wrong
                if not Ree.number.match(count):
                    self.logger.warning('[{}] Count {} is not a number, skip (url: {})'.format(task.name, count, task.url))
                    continue
                # replace if needed
                if count == '0':
                    count = self.const_zero_stock

                # UNIT
                unit = row.select('./span[@class="measure"]').text().strip()
                # replace
                if unit == '':
                    unit = 'ед.'

                # # check for '...' in item name
                # if item_name_class == 'long':
                #     item_name_long_url = urllib.parse.urljoin(self.domain, item_name_a_raw.attr('href'))
                #     self.logger.debug('[{}] Need parse full name, url: {} (name: {}, line: {})'.format(task.name, item_name_long_url, item_name, index))
                #     yield Task('parse_item_name', url=item_name_long_url, priority=95, raw=True, d_item_data={
                #         'count': count,
                #         'unit': unit,
                #         'price': price,
                #
                #         'index': index
                #     })
                #
                # else:
                #     # else OUTPUT with short name
                self.logger.debug('[{}] Item added, index {} at url {}'.format(task.name, index, task.url))
                self.result.append({
                    'name': item_name,
                    'count': count,
                    'unit': unit,
                    'price': price
                })

        except Exception as e:
            self._process_error(grab, task, e)

    # don't used, because its too expensive for network
    def task_parse_item_name(self, grab, task):
        self.logger.debug('[{}] Parse page: {}'.format(task.name, task.url))

        try:
            if self._check_body_errors(grab, task):
                if task.task_try_count < self.err_limit:
                    self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                    yield Task('parse_item_name', url=task.url, priority=105, task_try_count=task.task_try_count + 1, raw=True)
                else:
                    self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))

                return

            item_name_long_raw = grab.doc.select('//div[@class="big-wrapper"]/div[@class="content-page"]/div[@class="h1"]/h1')
            item_name_long = item_name_long_raw.text().strip()

            self.logger.debug('[{}] Item (longname) added, index {} at url {}'.format(task.name, task.d_item_data['index'], task.url))
            self.result.append({
                'name': item_name_long,
                'count': task.d_item_data['count'],
                'unit': task.d_item_data['unit'],
                'price': task.d_item_data['price']
            })

        except Exception as e:
            self._process_error(grab, task, e)