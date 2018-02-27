import re

from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from helpers.url_generator import UrlGenerator


VERSION = 28


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    re_unit = re.compile('\d+(?P<unit>.+)')

    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # parse global list
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # parse cats
            categories_list = grab.doc.select('//div[@class="main-links"]//p[@class="home_subcatalog_links_box"]/a')

            for link in categories_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {'SET_PAGE_COUNT': '99999'})
                yield self.do_task('parse_page', link, 90)

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

            # parse items links
            items_list = grab.doc.select('//div[@class="tovar-table tovar_basic"]//div[@class="tovar-col tovar2"]/a')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, 100, last=True)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse single item
    def task_parse_item(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # common block with info
            product_info = grab.doc.select('//div[@itemscope]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = count (quantity)
            # C = status (delivery)
            product_count_string = product_info.select('.//div[@class="popup-in"]/div[3]/p[1]').text('')

            # in stock
            if product_count_string == 'В наличии':
                product_count = '-1'
                product_status = '0'

            # on request without delivery days
            elif product_count_string == 'Под заказ':
                product_count = '-1'
                product_status = '-1'

            # on request with days...
            elif product_count_string != '':
                product_count_raw = Ree.extract_int.match(product_count_string)

                if not product_count_raw:
                    self.log.warning(task, f'Wrong delivery date {product_count_string}, skip...')
                    return

                product_count_raw = product_count_raw.groupdict()['int']

                # only [1..120] days
                if 1 <= int(product_count_raw) <= 120:
                    product_count = '-1'
                    product_status = product_count_raw

                else:
                    self.log.info(task, f'Skip delivery date {product_count_string}, skip...')
                    return

            else:
                self.log.warning(task, f'Unknown count status {product_count_string}, skip...')
                return

            # D = unit (measure) [const if no stock, else parse]
            product_unit_raw = DSpider.re_unit.search(product_info.select('.//div[@class="popup-in"]/div[3]/p[2]').text(''))

            if product_unit_raw:
                product_unit = product_unit_raw.groupdict()['unit'].strip()

            else:
                product_unit = 'ед.'

            # E = price
            product_price_raw = product_info.select('.//div[@class="popup-in"]//span[@class="price1 bold"]').attr('content', '')

            if not product_price_raw:
                self.log.warning(task, f'Unknown price #1 status {product_price_raw}, skip...')
                return

            if not Ree.float.match(product_price_raw):
                self.log.warning(task, f'Unknown price #2 status {product_price_raw}, skip...')
                return

            product_price = product_price_raw

            # F = vendor code (sku)
            product_vendor_code = product_info.select('.//span[@itemprop="sku"]').text('')

            # G = vendor (manufacture)
            tab_block = product_info.select('.//div[@id="tab1_"]')
            product_vendor = tab_block.select('.//dd[@itemprop="brand"]').text('')

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[@class="slider-for-cont"]/a[1]').attr('href', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # I = description (properties)
            product_description = {}

            table_keys = tab_block.select('.//dt')
            table_values = tab_block.select('.//dd')

            if table_keys and table_values:
                for index, row_keys in enumerate(table_keys):
                    product_description[row_keys.text('')] = table_values[index].text('')

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
            self.process_finally(task, last=True)
