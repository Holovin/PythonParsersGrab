from urllib.parse import urljoin
from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.el_parser import get_pagination
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

        # remove last char (dot for Re)
        self.const_page_param = Config.get('SITE_PAGE_PARAM')[:-1]

        self.const_price_on_request = Config.get('APP_PRICE_ON_REQUEST')
        self.const_stock_zero = Config.get('APP_STOCK_ZERO')
        # self.const_default_place = 'Полежаевская'

    def create_grab_instance(self, **kwargs):
        g = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, g)

    # fetch cats
    def task_initial(self, grab, task):
        self.logger.info('[{}] Initial url: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[{}] Err task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
            return

        try:
            cat_list = grab.doc.select('//div[@class="block-catalog"]//div[@class="tabs-content"]//a[contains(@href, "shop")]')

            # take links only for main cats, because its already contain all sub-cats items
            for row in cat_list:
                raw_link = row.attr('href')

                # skip sub-cats
                # cat:      /shop/cat/      -> 3
                # sub-cat:   /shop/cat/foo/  -> 4
                if raw_link.count('/') > 3:
                    continue

                # make absolute urls if needed
                if raw_link[:1] == '/':
                    raw_link = UrlGenerator.get_page_params(self.domain, raw_link, {
                        'section': '0',
                        'count': '50',
                        'sort': 'alphabet',
                        'order': 'asc',
                    })

                print(raw_link)
                yield Task(
                    'parse_items_v2',
                    url=raw_link,
                    priority=90,
                    raw=True,

                    d_base_url=raw_link,
                    d_page=1,
                    d_need_update_pagination=True)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.logger.info('[{}] Finish: {}'.format(task.name, task.url))

    # parse page & pagination
    def task_parse_items_v2(self, grab, task):
        self.logger.info('[{}] Start: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            if task.task_try_count < self.err_limit:
                self.logger.error('[{}] Restart task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
                yield Task(
                    'parse_items_v2',
                    url=task.url,
                    priority=95,
                    task_try_count=task.task_try_count + 1,
                    raw=True,

                    d_base_url=task.d_base_url,
                    d_page=task.d_page,
                    d_need_update_pagination=task.d_need_update_pagination,
                )
            else:
                self.logger.error('[{}] Skip task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))

            return

        try:
            # parse pagination numbers
            if task.get('d_need_update_pagination'):
                items = grab.doc.select('//a[contains(@href, "{}")]'.format(self.const_page_param))
                max_page, page_param = get_pagination(items, task.d_page)
                self.logger.info('[{}] Find max page: {}'.format(task.name, max_page))

                # example:
                # current page: 1
                # max visible: 5
                # [1] add: 2 3 4 as simple pages
                for p in range(task.d_page + 1, max_page - 1):
                    url = UrlGenerator.get_page_params(self.d_base_url, '', {
                        'section': '0',
                        'count': '50',
                        'sort': 'alphabet',
                        'order': 'asc',
                        'page': str(p)
                    })

                    yield Task(
                        'parse_items_v2',
                        url=url,
                        priority=100,
                        raw=True,

                        d_base_url=task.d_base_url,
                        d_page=p,
                        d_need_update_pagination=False,
                    )

                # [2] add: 5 with flag for parse
                if task.d_page < max_page:
                    url = UrlGenerator.get_page_params(self.d_base_url, '', {
                        'section': '0',
                        'count': '50',
                        'sort': 'alphabet',
                        'order': 'asc',
                        'page': str(max_page)
                    })

                    yield Task(
                        'parse_items_v2',
                        url=url,
                        priority=100,
                        raw=True,

                        d_base_url=task.d_base_url,
                        d_page=max_page,
                        d_need_update_pagination=True,
                    )

            return

            # parse items
            items_list = grab.doc.select('//div[@id="goods-list"]/tbody/tr')

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
