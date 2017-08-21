from urllib.parse import urljoin

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.el_parser import get_max_page
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init
from d_parser.helpers.re_set import Ree
from helpers.config import Config


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
from helpers.url_generator import UrlGenerator


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

        self.const_price_on_request = Config.get('APP_PRICE_ON_REQUEST')
        self.const_stock_zero = Config.get('APP_STOCK_ZERO')
        self.const_default_place = 'Полежаевская'

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, g)

    def task_initial(self, grab, task):
        self.logger.info('[{}] Initial url: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[{}] Err task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
            return

        try:
            cat_list = grab.doc.select('//ul[@class="catalog_nav_1"]//a[contains(@href, "catalog")]')

            for index, row in enumerate(cat_list):
                raw_link = row.attr('href')

                # make absolute urls if needed
                if raw_link[:1] == '/':
                    raw_link = urljoin(self.domain, raw_link)

                yield Task('parse_cat', url=raw_link, priority=90, raw=True)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.logger.info('[{}] Finish: {}'.format(task.name, task.url))

    def task_parse_cat(self, grab, task):
        self.logger.info('[{}] Start: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[{}] Err task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
            return

        try:
            cat_list = grab.doc.select('//div[@class="category_list"]//a[contains(@href, "catalog")]')

            for index, row in enumerate(cat_list):
                raw_link = row.attr('href')

                # make absolute urls if needed
                if raw_link[:1] == '/':
                    raw_link = urljoin(self.domain, raw_link)

                yield Task('parse_items', url=raw_link, priority=100, raw=True)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.logger.info('[{}] Finish: {}'.format(task.name, task.url))

    # def task_parse_page(self, grab, task):
    #     self.logger.info('[{}] Start: {}'.format(task.name, task.url))
    #
    #     if self._check_body_errors(grab, task):
    #         self.logger.fatal('[{}] Err task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
    #         return
    #
    #     try:
    #         items = grab.doc.select('//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM')))
    #         max_page = get_max_page(items, 1)
    #         self.logger.info('[{}] Find max page: {}'.format(task.name, max_page))
    #
    #         url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))
    #
    #         for p in range(1, max_page + 1):
    #             url = url_gen.get_page(p)
    #             yield Task('parse_items', url=url, priority=110)
    #
    #     except Exception as e:
    #         self._process_error(grab, task, e)
    #
    #     finally:
    #         self.logger.info('[{}] Finish: {}'.format(task.name, task.url))

    def task_parse_items(self, grab, task):
        self.logger.info('[{}] Start: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            if task.task_try_count < self.err_limit:
                self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                yield Task('parse_items', url=task.url, priority=105, task_try_count=task.task_try_count + 1, raw=True)
            else:
                self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))

            return

        try:
            # parse pagination numbers
            if not task.get('d_skip_page_check'):
                items = grab.doc.select('//a[contains(@href, "{}")]'.format(Config.get('SITE_PAGE_PARAM')))
                max_page = get_max_page(items, 1)
                self.logger.info('[{}] Find max page: {}'.format(task.name, max_page))

                url_gen = UrlGenerator(task.url, Config.get('SITE_PAGE_PARAM'))

                # self-execute from 2 page (if needed)
                for p in range(2, max_page + 1):
                    url = url_gen.get_page(p)
                    yield Task('parse_items', url=url, priority=100, d_skip_page_check=True, raw=True)

            # parse items
            items_list = grab.doc.select('//div[@class="cart_table"]/div/div/table/tbody/tr')

            for index, row in enumerate(items_list):
                try:
                    # NAME
                    item_name = row.select('./td[1]//div[@class="description"]/div/a').text().strip()

                    # UNIT
                    unit = row.select('./td[2]').text().strip()
                    if unit == '':
                        unit = 'ед.'

                    # PRICE
                    price_raw = row.select('./td[6]//meta[@itemprop="lowprice"]').attr('content')
                    match = Ree.float.match(price_raw)
                    # check & fix
                    if not match:
                        self.logger.warning('[{}] Skip item, because price is {} (line: {})'.format(task.name, price_raw, index))
                        continue

                    price = match.groupdict()['price'].replace(',', '.')

                    # COUNT
                    count = row.select('./td[5]')
                    count_text = count.text().strip()

                    # case 1: string line
                    if count_text == 'распродано':
                        item_count = self.const_price_on_request
                        item_place = self.const_default_place

                        # OUTPUT
                        self.logger.debug('[{}] Item added, index {} at url {}'.format(task.name, index, task.url))
                        self.result.append({
                            'name': item_name,
                            'count': item_count,
                            'unit': unit,
                            'price': price,
                            'place': item_place
                        })

                    # case 2: string line
                    elif count_text == 'под заказ':
                        item_count = self.const_stock_zero
                        item_place = self.const_default_place
                        # OUTPUT
                        self.logger.debug('[{}] Item added, index {} at url {}'.format(task.name, index, task.url))
                        self.result.append({
                            'name': item_name,
                            'count': item_count,
                            'unit': unit,
                            'price': price,
                            'place': item_place
                        })

                    # case 3
                    else:
                        count_rows = count.select('.//div[@class="layer_info"]/table/tbody/tr')

                        for count_row in count_rows:
                            item_place = count_row.select('./td[1]').text().strip()
                            item_count = 0

                            # add stock
                            place_count_stock = count_row.select('./td[1]').text().strip()
                            if Ree.float.match(place_count_stock):
                                item_count += float(place_count_stock)

                            # add expo
                            place_count_expo = count_row.select('./td[2]').text().strip()
                            if Ree.float.match(place_count_expo):
                                item_count += float(place_count_expo)

                            if item_count > 0:
                                # OUTPUT
                                self.logger.debug('[{}] Item added, index {} at url {}'.format(task.name, index, task.url))
                                self.result.append({
                                    'name': item_name,
                                    # 3.140 -> 3.14; 3.0 -> 3
                                    'count': '{0:g}'.format(item_count),
                                    'unit': unit,
                                    'price': price,
                                    'place': item_place
                                })
                except IndexError as e:
                    self.logger.warning('[{}] Skip item: {}, {}'.format(task.name, type(e).__name__, task.url))

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.logger.info('[{}] Finish: {}'.format(task.name, task.url))
