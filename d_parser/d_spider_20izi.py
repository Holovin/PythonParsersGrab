import re

from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from helpers.url_generator import UrlGenerator
from d_parser.helpers.stat_counter import StatCounter as SC


VERSION = 29


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    re_product_unit = re.compile('^.+\d\s(?P<unit>.+)$')

    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # prepare
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # make link
            url = UrlGenerator.get_page_params(self.domain, 'catalog', {'curPos': 0})

            # prepare page loop parsing
            yield self.do_task('parse_page', url, DSpider.get_next_task_priority(task))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # parse table rows
            table = grab.doc.select('//table[@class="table search_table list"]//tr')

            # parse table links to items
            items_links = table.select('.//a[starts-with(@href, "/catalog/catalog")]')

            for index, row in enumerate(items_links):
                link = row.attr('href')

                # make absolute urls if needed
                if link[:1] == '/':
                    link = UrlGenerator.get_page_params(self.domain, link, {})

                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

            # parse "показать ещё" links
            more_links = grab.doc.select('.//a[starts-with(@href, "/catalog/?")]')

            # hope it will be only 0 or 1 link
            for index, row in enumerate(more_links):
                link = row.attr('href')

                # make absolute urls if needed
                if link[:1] == '/':
                    link = UrlGenerator.get_page_params(self.domain, link, {})

                yield self.do_task('parse_page', link, DSpider.get_next_task_priority(task, 0))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse single item
    def task_parse_item(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # common block with info
            product_info = grab.doc.select('//div[@class="product_info"]')

            # parse fields
            # A = name
            product_name = product_info.select('./h2[1]').text()

            # B = count (quantity)
            # C = status (delivery)
            # D = unit (measure) [const if no stock, else parse]
            product_count_string = product_info.select('./div[@class="info_element total"]/div[@class="color_green"]').text()

            if product_count_string == 'Нет в наличии':
                product_count = '-1'
                product_status = '-1'
                product_unit = 'ед.'

            else:
                product_count = Ree.extract_int.match(product_count_string).groupdict()['int']
                product_status = '0'
                product_unit = DSpider.re_product_unit.match(product_count_string).groupdict()['unit']

            # E = price
            product_price_raw = product_info.select('./div[@class="info_element total"]/div[@class="total_prise"]/span').text()
            product_price = product_price_raw.replace(' ', '')

            # check if correct price
            if not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Skip item, cuz wrong price {product_price}', task)
                return

            # F = vendor code (sku)                                                                         what's wrong with python xpath?
            product_vendor_code = product_info.select('./div[contains(@class, "info_elements_row")]/div[@class="info_element"][1]/node()[4]').text().strip()

            # G = vendor (manufacture)
            product_vendor = product_info.select('./div[contains(@class, "info_elements_row")]/div[@class="info_element"][3]/a').text().strip()

            # H = photo url
            product_photo_url_raw = grab.doc.select('//div[contains(@class, "product_slider")]/div[@class="img_holder"]/div[1]/img').attr('src')
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})

            # I = description (properties) [const empty]
            product_description = ' '

            # ID
            product_id = Ree.extract_int.match(task.url).groupdict()['int']

            # save
            self.result.add({
                'name': product_name,
                'quantity': product_count,
                'delivery': product_status,
                'measure': product_unit,
                'price': product_price,
                'sku': product_vendor_code,
                'manufacture': product_vendor,
                'photo': product_photo_url,
                'id': product_id,
                'properties': product_description,
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
