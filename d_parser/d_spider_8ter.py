from grab import Grab

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

            items_list = grab.doc.select('//div[@id="catalog-groups"]//div[@class="catalog-group-name"]/a')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_page', link,  DSpider.get_next_task_priority(task))

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

            # parse items links
            items_list = grab.doc.select('//div[@id="catalog-groups"]//div[@itemprop="name"]/a')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

            # parse next page link -->                                                                   vvv   looks bad  vvv
            next_page = grab.doc.select('(//ul[@class="pager"])[1]/li[contains(@class, "pager-current")]/following-sibling::li[1]/a[@title]').attr('href', '')

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
            product_info = grab.doc.select('//div[@itemtype="http://schema.org/Product"]')

            # parse fields

            # A = name
            product_name = product_info.select('.//div[@class="product-title-full"]').text()

            # D = unit (measure)
            product_unit = product_info.select('.//label[@for="edit-quantity--2"]').text('ед.').replace('Количество, ', '')

            # E = price
            product_price = product_info.select('.//span[@itemprop="price"]').attr('data-price', '')

            if not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # F = vendor code (sku)
            product_vendor_code = product_info.select('.//div[contains(@class, "field-name-field-code")]//div[@class="field-items"]').text('')

            # G = vendor (manufacture)
            product_vendor = grab.doc.select('//div[@class="breadcrumb"]//a[last()]').text('')

            # H = photo url
            product_photo_url_raw = product_info.select('.//img[@itemprop="image"]').attr('src', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # ID
            product_id = product_info.select('.//input[@name="product_id"]').attr('value', '')

            # I = description (properties)
            product_description = {}
            table = product_info.select('.//li[@id="tab-full-properties"]//div[@class="block-th-item"]')

            for row in table:
                key = row.select('./div[@class="block-th-property-title"]').text('')
                value = row.select('./div[@class="block-th-property-value"]').text('')

                if key:
                    product_description[key] = value

            ###
            # B = count (quantity) [-1 if all ok]
            # C = status (delivery)
            product_count_string = product_info.select('string(.//div[@id="product-availability-block"]/span[contains(@class, "product-status-")]/@class)').text('')
            product_count_string_checker = product_info.select('.//div[@id="product-availability-block"]').text('')
            product_count = '-1'
            product_status = None

            store_statuses = {
                'Новая Москва, пос. Коммунарка, ул. Александры Монаховой, вл. 2': '?',
                '41 км МКАД. Рынок «Славянский мир», пав. Пассаж 5.': '?',
                'Серпуховский район, деревня Борисово, Данковское шоссе д. 3А, стр. 1': '?',
                'Московская область, г. Одинцово, ул. Внуковская, д. 11, Строительный рынок «АКОС»': '?',
                'Московская область, г. Люберцы, ул. Котельническая, д. 18': '?',
                'Красногорский район, пос. Нахабино, Волоколамская ул. д. 1Б': '?',
                'Московская область, г. Домодедово, ул. Лесная, д. 23': '?',
                'Московская область, г. Королев, ул. Пионерская, д. 1А': '?',
            }

            # skip additional parse
            if product_count_string in ['product-status-out-of-stock', 'product-availability-block', 'product-status-orderable'] \
                    or 'Москва: нет в наличии' in product_count_string_checker:
                product_status = '-1'

            # need additional
            elif product_count_string == 'product-status-available':
                table = product_info.select('(//div[@class="stocks-data-wrapper"])[1]//div[@class="delivery-option stores"]//tr[not(th)]')

                for row in table:
                    key = row.select('./td[@class="stock-name"]').text('')
                    value = row.select('./td[contains(@class, "product-quantity")]').text('')

                    if key:
                        store_statuses[key] = '0' if value == 'Есть' else '-1'

            else:
                self.log_warn(SC.MSG_UNKNOWN_STATUS, f'Unknown status class "{product_count_string}"', task)
                return

            # save
            for store_name, store_local_status in store_statuses.items():
                # use global status if -1
                if product_status == '-1':
                    local_status = '-1'

                # try parse
                else:
                    if store_local_status == '?':
                        self.log_warn(SC.MSG_UNKNOWN_STATUS, f'Store status is not defined!!!', task)
                        continue

                    local_status = store_local_status

                # save
                self.result.add({
                    'name': product_name,
                    'quantity': product_count,
                    'delivery': local_status,
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
