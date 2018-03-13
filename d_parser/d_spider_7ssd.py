from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from d_parser.helpers.stat_counter import StatCounter as SC
from helpers.url_generator import UrlGenerator


VERSION = 29


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # fetch categories
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # catalog
            catalog = grab.doc.select('//div[@class="main__sidebar"]/ol//a[not(@href="#")]')

            for link in catalog:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_cat_page', link, DSpider.get_next_task_priority(task))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page categories
    def task_parse_cat_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            catalog = grab.doc.select('//div[@class="cats-wrap"]//a')

            for link in catalog:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_page_items', link, DSpider.get_next_task_priority(task))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page items in category
    def task_parse_page_items(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            items = grab.doc.select('//div[@class="items-wrap"]//div[@class="item__title"]//a')

            for link in items:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

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
            product_info = grab.doc.select('//div[@class="main__content"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = count (quantity)
            # C = status (delivery)
            product_count_string = product_info.select('.//div[@class="data-store"]')
            product_count = None

            store_count = {
                'data-msk': 0,
                'data-nsb': 0,
                'data-krd': 0,
            }

            for city in store_count:
                temp = product_count_string.attr(city, '').replace(' ', '')

                if temp != '' or not Ree.float.match(temp):
                    if product_count is None:
                        product_count = 0

                    temp = float(temp)

                    if temp >= 0:
                        # fix
                        if temp == 0:
                            store_count[city] = -1

                        product_count += temp
                    else:
                        self.log_warn(SC.MSG_POSSIBLE_WARN, f'Unknown count status (>=0) {product_count_string.html()} skip...', task)
                        continue

            if product_count is None:
                self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Unknown count status {product_count_string.html()} skip...', task)
                return

            elif product_count == 0:
                product_count = '-1'
                product_status = '-1'

            else:
                product_count = '-1'
                product_status = '0'

            # D = unit (measure)
            product_unit = product_info.select('.//input[contains(@class, "product_count")]').attr('placeholder', 'ед.')

            # E = price
            product_price = product_info.select('.//strong[@id="item_price1"]').attr('content', '')

            if not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # F = vendor code (sku)
            product_vendor_code = product_info.select('.//div[@class="item-number"]/strong').text('')

            # G = vendor (manufacture) [const]
            product_vendor = ''

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[@class="fotorama"]/a[1]').attr('href', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # ID
            product_id = product_info.select('.//a[@id="btn_buy"]').attr('data-id', '')

            # I = description (properties)
            product_description = {
                'Описание': product_info.select('.//div[@itemprop="description"]').text('')
            }

            # I - first table
            table_characteristics = product_info.select('.//div[@data-id="#characteristics"]')

            for row in table_characteristics.select('.//tr'):
                key = row.select('./td[1]').text('')
                value = row.select('./td[2]').text('')

                # default save
                if key:
                    product_description[key] = value

            # I - second table
            table_log = product_info.select('.//div[contains(@class, "logistick")]')

            for row in table_log.select('.//tr'):
                key = row.select('./td[1]').text('')
                value = row.select('./td[2]').text('')

                # default save
                if key:
                    product_description[key] = value

            # save
            for store_name, value in store_count.items():
                self.result.add({
                    'name': product_name,
                    'quantity': value,
                    'delivery': product_status,
                    'measure': product_unit,
                    'price': product_price,
                    'sku': product_vendor_code,
                    'manufacture': product_vendor,
                    'photo': product_photo_url,
                    'id': product_id,
                    'properties': product_description,
                    'place': store_name
                })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
