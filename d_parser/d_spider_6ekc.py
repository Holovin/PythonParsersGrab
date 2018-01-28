import re

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init, extend_class, check_errors, process_finally
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator


VERSION = 27


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')

    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')

        extend_class(DSpider, [
            check_body_errors,
            check_errors,
            process_error,
            process_finally,
            common_init
        ])

        self.common_init(try_limit)

    def create_grab_instance(self, **kwargs):
        grab = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, grab)

    # Fetch all categories from main page
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                self.log.fatal(task, f'Err task, attempt {task.task_try_count}')
                return

            category_list = grab.doc.select('//div[@id="categories_block_left"]/div[1]//a')

            for link in category_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield Task('parse_page', url=link, priority=90, raw=True)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)

            # parse items links
            items_list = grab.doc.select('//table[@class="prod"]//tr[not(contains(@class, "white"))]')

            # if all page with useless records - skip other pages
            success_pages = 0

            for index, row in enumerate(items_list):
                # check row
                status = row.select('./td[2]')
                price = row.select('./td[3]')

                if status == '0' or price == 'под заказ':
                    self.log.warning(task, f'Skip item, because status {status} / {price}')
                    continue

                link = row.select('./td[@class="name"]/a').attr('href')
                link = UrlGenerator.get_page_params(self.domain, link, {})

                success_pages += 1
                yield Task('parse_item', url=link, priority=100, raw=True)

            # parse next page if current is ok
            if success_pages > 0:
                next_page = grab.doc.select('//div[@class="pagination"][1]//a[@class="next_page_link"]').attr('href', '')

                if next_page:
                    next_page = UrlGenerator.get_page_params(self.domain, next_page, {})
                    yield Task('parse_page', url=next_page, priority=90, raw=True)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse single item
    def task_parse_item(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)

            product_info = grab.doc.select('//div[@id="product_right"]')

            # COMMON FIELDS
            # F = vendor code [const = skip for parsing]
            product_vendor_code = ' '

            # G = vendor [const = skip for parsing]
            product_vendor = ' '

            # H = photo url
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_info.select('//img[@id="bigpic"]').attr('src', ''), {})

            # I = description
            product_description = {'Описание': product_info.select('.//div[@id="idTab1"]').text(default=' ')}

            # whats wrong with this site? div - tabid1, ul - tabid2 ???
            table = product_info.select('//ul[@id="idTab2"]/li')

            for row in table:
                key = row.select('./label/text()').text()
                value = row.select('./span').text()

                if key:
                    product_description[key] = value

            if not product_photo_url:
                self.log.warning(task, f'Skip photo url')

            # SPECIAL FIELDS
            # special section, because this site contains several products on page
            products_table = product_info.select('.//table[@class="prod"]//tr[contains(@class, "product")]')

            # parse fields
            for product_row in products_table:
                # A = name
                product_name = product_row.select('./td[@class="name"]').text()

                # B = count
                # C = status
                product_count_string = product_row.select('.//span[@class="stock"]').text(default='')

                if not product_count_string or not Ree.number.match(product_count_string):
                    self.log.warning(task, f'Skip item (1), because count is {product_count_string}')
                    return

                product_count_int = int(product_count_string)

                if product_count_int <= 0:
                    self.log.warning(task, f'Skip item (2), because count is {product_count_string}')
                    return

                if product_count_int == 1:
                    product_count = '-1'
                    product_status = '-1'
                else:
                    product_count = product_count_string
                    product_status = '0'

                # D = unit
                product_unit = product_row.select('./td[@class="but"]/form[@class="variants"]//tr/td[2]').text(default='ед.')

                # E = price
                product_price = product_row.select('./td[@class="pr"]/span[@class="price"]').text()

                # check if positive and correct price
                if not Ree.float.match(product_price):
                    self.log.debug(task, f'Skip item, cuz wrong price {product_price}')
                    return

                # save
                self.result.append({
                    'name': product_name,
                    'quantity': product_count,
                    'delivery': product_status,
                    'measure': product_unit,
                    'price': product_price,
                    'sku': product_vendor_code,
                    'manufacture': product_vendor,
                    'photo': product_photo_url,
                    'properties': product_description
                })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
