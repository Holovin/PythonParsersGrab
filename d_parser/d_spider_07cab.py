from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from helpers.url_generator import UrlGenerator
from d_parser.helpers.stat_counter import StatCounter as SC


VERSION = 29


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # parse global list
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # parse items
            items_list = grab.doc.select('//div[@class="products-wrap"]//a[@itemprop="url" and @class="products-name"]')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

            # parse next page link
            next_page = grab.doc.select('//div[contains(@class, "pagination")][1]//a[@class="pg-next" and contains(@href, "p=")]').attr('href', '')

            if next_page:
                next_page = UrlGenerator.get_page_params(self.domain, next_page, {})
                yield self.do_task('initial', next_page, DSpider.get_next_task_priority(task, 0))

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
            product_info = grab.doc.select('//div[@id="product"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = count (quantity)
            # C = status (delivery)
            product_count_string_stock = product_info.select('.//span[contains(@class, "in-stock")]').text(default='')
            product_count_string_order = product_info.select('.//span[contains(@class, "under-order")]').text(default='')

            # D = unit (measure) [const if no stock, else parse]
            if product_count_string_stock and product_count_string_stock[-1] == 'м':
                product_unit = 'м'
                product_count_string_stock = product_count_string_stock[:-1].strip()
            else:
                product_unit = 'ед.'

            if product_count_string_stock.isdigit():
                product_count = product_count_string_stock
                product_status = '0'

            elif product_count_string_order == 'под заказ':
                product_count = '-1'
                product_status = '-1'

            else:
                self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Unknown count status {product_count_string_stock} or {product_count_string_order}, skip...', task)
                return

            # E = price
            product_price_raw = product_info.select('.//p[@class="summ"]').text(default='')

            if not product_price_raw:
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price_raw}, skip...', task)
                return

            if product_price_raw == 'по запросу':
                product_price = '-1'

            else:
                # parse number from child node
                product_price_raw = product_info.select('.//p[@class="summ"]/span[@id="commmon_price"]').text(default='')

                if not product_price_raw or not Ree.float.match(product_price_raw):
                    self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price_raw}, skip...', task)
                    return

                product_price = product_price_raw

            # F = vendor code (sku) [const]
            product_vendor_code = ''

            # G = vendor (manufacture) [const]
            product_vendor = ''

            # H = photo url
            product_photo_url_raw = product_info.select('.//img[@itemprop="image"]').attr('src')
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})

            # I = description (properties)
            product_description = {}

            # I :: Base
            table = product_info.select('.//div[@class="tab-content-list"]')

            for row in table:
                key = row.select('./span[1]').text(default=None)
                value = row.select('./span[2]').text(default=None)

                if key and value and key != 'Наличие':
                    product_description[key] = value

            # I :: description
            description = product_info.select('.//div[@id="opisanie"]').text(default='')
            if description:
                product_description['Описание'] = description

            # I :: using
            description = product_info.select('.//div[@id="primenenie"]').text(default='')
            if description:
                product_description['Применение'] = description

            # I :: tech
            description = product_info.select('.//div[@id="tehnicheskie_harakteristiki"]').text(default='')
            if description:
                product_description['Технические характеристики'] = description

            # ID
            product_id = Ree.extract_int.match(product_info.select('.//a[@class="btn btn-success btn-large"]').attr('onclick', ''))

            if product_id:
                product_id = product_id.groupdict()['int']
            else:
                product_id = ''

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
                'properties': product_description
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
