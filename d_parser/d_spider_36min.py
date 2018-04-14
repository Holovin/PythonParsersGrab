from selection import SelectorList

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

    # fetch items
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            items_list = grab.doc.select('//div[contains(@class, "left-menu")]//li/a')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {'COUNT': '100'})
                yield self.do_task('parse_page', link, DSpider.get_next_task_priority(task))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page items
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # parse items links                                   vv  TABULATION  vv
            items_list = grab.doc.select('//div[contains(@class, "	catalog-list	")]//a[@class="title-list-item"]')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

            # parse next page link
            next_page = grab.doc.select('(//div[contains(@class, " catalog-list ")]//a[@class="modern-page-next next-page"])[1]').attr('href', '')

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
            product_info = grab.doc.select('//div[contains(@class, "	single-product-page	")]')

            # A = name
            product_name = product_info.select('.//h1').text()

            # I = description (properties)
            # + D, F, G
            product_all_spec_table = product_info.select('.//div[contains(@class, "all-specifications")]//tr')
            product_description = {}

            product_unit = 'ед.'
            product_vendor = ''
            product_vendor_code = ''

            for row in product_all_spec_table:
                store_name = row.select('./td[@class="heading-text"]').text('')
                value = row.select('./td[@class="specification-text"]').text('')

                if store_name and value:
                    product_description[store_name] = value

                if store_name == 'Единица измерения':
                    # D = unit (measure)
                    product_unit = value

                elif store_name == 'Артикул поставщика':
                    # F = vendor code (sku)
                    product_vendor_code = value

                elif store_name == 'Бренд':
                    # G = vendor (manufacture)
                    product_vendor = value

            # E = price
            product_price = product_info\
                .select('.//div[@class="price-block__pricePerCard"]/span[@class="price-style"]')\
                .text()\
                .replace(' руб.', '')\
                .replace(',', '.')

            # if product_price == 'На заказ':
            if not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[contains(@class, "page-photo")]//img').attr('src', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # ID
            product_id = product_info.select('(.//a[contains(@class, "add-url-buy")])[1]').attr('data-offers-add', '')

            # City parser
            product_table_city = grab.doc.select('//div[@id="block-for-city"]//p[@class="stock-info"]')

            # Region parser
            product_table_region = grab.doc.select('//div[@id="block-for-warehouses"]//div[contains(@class, "toggle-link-block")]/div//p[@class="stock-info"]')

            product_count = {}
            self.for_store_in(product_table_city, product_count, task)
            self.for_store_in(product_table_region, product_count, task)

            if len(set(product_count.values())) == 1:
                self.log_warn(SC.MSG_UNKNOWN_STATUS, f'All store was skipped, seems useless item', task)
                return

            # B + C
            # B = count (quantity) [-1 if all ok]
            # C = status (delivery)
            for store_name, store_count in product_count.items():
                # save
                self.result.add({
                    'name': product_name,
                    'quantity': store_count,
                    'delivery': '-1' if store_count == '-1' else '0',
                    'measure': product_unit,
                    'price': product_price,
                    'sku': product_vendor_code,
                    'manufacture': product_vendor,
                    'photo': product_photo_url,
                    'properties': product_description,
                    'id': product_id,
                    'place': store_name,
                })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    def for_store_in(self, table: SelectorList, product_count: {}, task) -> None:
        for store in table:
            store_name = store.select('./text()').text('')

            if not store_name:
                self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Empty store name, skip...', task)
                continue

            store_count = store.select('./span').text('').strip('() ')

            if store_count == 'нет на складе':
                product_count[store_name] = '-1'
                continue

            store_count_int = Ree.extract_int.match(store_count)

            if not store_count_int:
                self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Wrong count value {store_count}, skip...', task)
                continue

            store_count = store_count_int.groupdict()['int']

            product_count[store_name] = store_count
