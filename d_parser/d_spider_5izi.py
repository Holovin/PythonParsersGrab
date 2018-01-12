import re

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init, check_errors
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator


VERSION = 26


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')
    re_product_unit = re.compile('^.+\d\s(?P<unit>.+)$')

    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')
        DSpider._check_body_errors = check_body_errors
        DSpider._check_errors = check_errors
        DSpider._process_error = process_error
        DSpider._common_init = common_init
        self._common_init(try_limit)

        Ree.init()

    def create_grab_instance(self, **kwargs):
        grab = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, grab)

    # prepare
    def task_initial(self, grab, task):
        self.logger.info('[{}] Initial url: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            self.logger.fatal('[{}] Err task with url {}, attempt {}'.format(task.name, task.url, task.task_try_count))
            return

        try:
            # make link
            url = UrlGenerator.get_page_params(self.domain, 'catalog', {
                'curPos': 0
            })

            # prepare page loop parsing
            yield Task(
                'parse_page',
                url=url,
                priority=90,
                raw=True)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.logger.info('[{}] Finish: {}'.format(task.name, task.url))

    # parse page
    def task_parse_page(self, grab, task):
        self.logger.info('[{}] Start: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            yield self._check_errors(task)

        try:
            # parse table rows
            table = grab.doc.select('//table[@class="table search_table list"]//tr')

            # parse table links to items
            items_links = table.select('.//a[starts-with(@href, "/catalog/catalog")]')

            for index, row in enumerate(items_links):
                link = row.attr('href')

                # make absolute urls if needed
                if link[:1] == '/':
                    link = UrlGenerator.get_page_params(self.domain, link, {})

                yield Task(
                    'parse_item',
                    url=link,
                    priority=100,
                    raw=True)

            # parse "показать ещё" links
            more_links = grab.doc.select('.//a[starts-with(@href, "/catalog/?")]')

            # hope it will be only 0 or 1 link
            for index, row in enumerate(more_links):
                link = row.attr('href')

                # make absolute urls if needed
                if link[:1] == '/':
                    link = UrlGenerator.get_page_params(self.domain, link, {})

                yield Task(
                    'parse_page',
                    url=link,
                    priority=90,
                    raw=True)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.logger.info('[{}] Finish: {}'.format(task.name, task.url))

    # parse single item
    def task_parse_item(self, grab, task):
        self.logger.info('[{}] Start: {}'.format(task.name, task.url))

        if self._check_body_errors(grab, task):
            yield self._check_errors(task)

        try:
            # common block with info
            product_info = grab.doc.select('//div[@class="product_info"]')

            # parse fields
            # A = name
            product_name = product_info.select('./h2[1]').text()

            # B = count
            # C = status
            # if B = [0...100] => [0...100]
            # if B > 100 => 100
            # D = unit [const if no stock, else parse]
            product_count_string = product_info.select('./div[@class="info_element total"]/div[@class="color_green"]').text()

            if product_count_string == 'Нет в наличии':
                product_count = 'zapros'
                product_status = 'zakaz'
                product_unit = 'ед.'

            else:
                product_count = Ree.extract_int.match(product_count_string).groupdict()['int']
                product_status = '000000000'
                product_unit = DSpider.re_product_unit.match(product_count_string).groupdict()['unit']  # 'штук'  # TODO: parse?

            # E = price
            product_price_raw = product_info.select('./div[@class="info_element total"]/div[@class="total_prise"]/span').text()
            product_price = product_price_raw.replace(' ', '')

            # check if correct price
            if not Ree.float.match(product_price):
                self.logger.debug('[{}] Skip item, cuz wrong price {}'.format(task.name, product_price))
                return

            # F = vendor code                                                                                what's wrong with python xpath?
            product_vendor_code = product_info.select('./div[contains(@class, "info_elements_row")]/div[@class="info_element"][1]/node()[4]').text().strip()

            # G = vendor
            product_vendor = product_info.select('./div[contains(@class, "info_elements_row")]/div[@class="info_element"][3]/a').text().strip()

            # H = photo url
            product_photo_url_raw = grab.doc.select('//div[contains(@class, "product_slider")]/div[@class="img_holder"]/div[1]/img').attr('src')
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})

            # I = description [const empty]
            product_description = ' '

            # save
            self.result.append({
                'name': product_name,
                'count': product_count,
                'status': product_status,
                'unit': product_unit,
                'price': product_price,
                'vendor_code': product_vendor_code,
                'vendor': product_vendor,
                'photo_url': product_photo_url,
                'description': product_description
            })

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.logger.info('[{}] Finish: {}'.format(task.name, task.url))
