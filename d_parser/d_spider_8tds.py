from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from helpers.url_generator import UrlGenerator


VERSION = 28


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # fetch items
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            items_list = grab.doc.select('//div[contains(@class, "goodsGoods")]//a[@class="textTitle"]')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, 100, last=True)

            # parse next page link
            next_page = grab.doc.select('//a[contains(text(), "»")]').attr('href', '')

            if next_page:
                next_page = UrlGenerator.get_page_params(self.domain, next_page, {})
                yield self.do_task('initial', next_page, 90)

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
            product_count_string = product_info.select('.//span[@itemprop="availability"]').text('')

            if 'шт.' in product_count_string or 'м.п.' in product_count_string or product_count_string in ['есть', 'в наличии']:
                product_count = '-1'
                product_status = '0'

            elif 'срок поставки' in product_count_string or product_count_string in ['НЕТ', 'нет']:
                self.log.info(task, f'Skip count status {product_count_string} skip...')
                return

            else:
                self.log.warning(task, f'Unknown count status {product_count_string} skip...')
                return

            # D = unit (measure)
            product_unit = product_info.select('.//form[@class="form_addCart"]//span[@class="measure"]').text('ед.')

            # E = price
            product_price = product_info.select('.//form[@class="form_addCart"]//meta[@itemprop="price"]').attr('content', '')

            if not product_price or not Ree.float.match(product_price):
                self.log.warning(task, f'Unknown price status {product_price}, skip...')
                return

            # F = vendor code (sku)
            product_vendor_code = product_info.select('.//span[@class="articleValue"]').text('')

            # G = vendor (manufacture)
            product_vendor = product_info.select('.//a[@itemprop="brand"]').text('')

            # H = photo url
            product_photo_url_raw = product_info.select('.//img[@itemprop="image"]').attr('src', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # I = description (properties)
            product_description = {'Описание': product_info.select('.//div[@class="content"][1]').text('')}

            # ID
            product_id = product_info.select('.//input[@name="addcart"]').attr('value', '')

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
                'properties': product_description,
                'id': product_id,
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task, last=True)
