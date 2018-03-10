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
            catalog = grab.doc.select('//div[@id="categories"]//a')

            for link in catalog:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_page', link, DSpider.get_next_task_priority(task))

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

            catalog = grab.doc.select('//div[@class="catalog_section "]')

            # parse items links
            items_list = catalog.select('.//div[@class="product_item"]//a')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

            # parse next page link
            next_page = catalog.select('//a[@class="next_page"]').attr('href', '')

            if next_page:
                next_page = UrlGenerator.get_page_params(self.domain, next_page, {})
                yield self.do_task('parse_page', next_page, DSpider.get_next_task_priority(task, 0))

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
            product_info = grab.doc.select('//div[@class="catalog_single_item"]')

            # parse fields
            # A = name
            product_name = product_info.select('./h1').text()

            # B = count (quantity)
            # C = status (delivery)
            product_count_string = product_info.select('.//div[@id="technical_chars"]//span[contains(@class, "available")]').text('')

            if product_count_string == 'В наличии':
                product_count = '-1'
                product_status = '0'

            elif product_count_string == 'На заказ':
                product_count = '-1'
                product_status = '-1'

            elif product_count_string != '':
                product_count_raw = Ree.extract_int.match(product_count_string)
                product_status = '0'

                if product_count_raw:
                    product_count = product_count_raw.groupdict()['int']
                else:
                    self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Unknown count status {product_count_string}, skip...', task)
                    return

            else:
                self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Unknown count status {product_count_string} skip...', task)
                return

            # E = price
            product_price = product_info.select('.//ins[@class="price-rouble"]').text('')

            if product_price == 'по запросу':
                product_price = '-1'

            if not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # H = photo url
            product_photo_url_raw = product_info.select('//div[@class="slider_item"]/a').attr('href', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # I = description (properties)
            product_description = {}

            # try parse full props
            table = product_info.select('//div[@id="technical_chars"]//table//table//tr')

            # D = unit (measure)
            product_unit = 'ед.'

            # F = vendor code (sku)
            product_vendor_code = ''

            # G = vendor (manufacture)
            product_vendor = ''

            for row in table:
                key = row.select('./td[1]').text('')
                value = row.select('./td[2]').text('')

                if key:
                    if key == 'Основная ЕИ':
                        product_unit = value

                    elif key == 'Артикул':
                        product_vendor_code = value

                    elif key == 'Бренд':
                        product_vendor = value.replace('. Посмотреть все товары этого бренда', '')

                    product_description[key] = value

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
                'properties': product_description
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
