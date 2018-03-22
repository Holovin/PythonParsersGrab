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

    # fetch categories
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # catalog
            catalog = grab.doc.select('//div[@class="workarea"]//div[contains(@class, "catalog-section-title")]/a')

            for link in catalog:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {'limit': 900, 'view': 'price'})
                yield self.do_task('parse_page', link, DSpider.get_next_task_priority(task))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page pagination
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            items_list = grab.doc.select('//div[@class="catalog-item-price-view"]//a[@itemprop="url"]')

            for link in items_list:
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
            product_info = grab.doc.select('//div[@class="workarea"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = count (quantity)
            # C = status (delivery)
            product_count_string = product_info.select('.//meta[@itemprop="availability"]').attr('content', '')

            if product_count_string == 'InStock':
                product_count = '-1'
                product_status = '0'

            else:
                self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Unknown count status {product_count_string} skip...', task)
                return

            # D = unit (measure)
            product_unit = product_info.select('.//div[@class="catalog-detail-price"]//span[@class="unit"]').text('ед.').replace('руб. за ', '')

            # E = price
            product_price = product_info.select('.//div[@class="catalog-detail-price"]//meta[@itemprop="price"]').attr('content', '')

            if not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # F = vendor code (sku)
            product_vendor_code = product_info.select('.//div[@class="catalog-detail"]//div[@class="article"]').text('').replace('Артикул: ', '')

            # G = vendor (manufacture)
            product_vendor = product_info.select('.//a[starts-with(@href, "/vendors")]').text('')

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[@class="detail_picture"]//meta[@itemprop="image"]').attr('content', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # I = description (properties)
            product_description = {}

            # try parse full props
            for row in product_info.select('.//div[@class="catalog-detail-property"]'):
                key = row.select('./span[@class="name"]').text()
                value = row.select('./span[@class="val"]').text()

                if key and value:
                    product_description[key] = value

            # ID
            product_id = product_info.select('.//input[@name="ID"]').attr('value', '')

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
