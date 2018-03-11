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

            items_list = grab.doc.select('//div[@class="catalog-holder"]//a[img]')

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
            items_list = grab.doc.select('//div[@id="product-list"]//a[@itemprop="url"]')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

            # parse next page link
            next_page = grab.doc.select('(//div[@class="block lazyloading-paging"])[1]//li[last()]/a[@class="inline-link"]').attr('href', '')

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
            product_info = grab.doc.select('//div[@class="main"]')

            # parse fields
            # ID
            product_id = product_info.select('.//input[@name="product_id"]').attr('value', '')
            product_sku = product_info.select('.//input[@name="sku_id"]').attr('value', '')

            # A = name
            product_name = product_info.select('.//h1').text()

            # B = count (quantity)
            # C = status (delivery)
            # TODO: somehow handle stats?
            grab_product_count = Grab()
            url = UrlGenerator.get_page_params(self.domain, '/gotinstockget/', {})
            grab_product_count.go(url, post=[
                ('sku_id', product_sku),
                ('product_id', product_id),
                ('quantity', '1')
            ])

            if grab_product_count.doc.body == '' or grab_product_count.doc.code != 200:
                self.log_warn(SC.MSG_UNKNOWN_STATUS, f'Wrong answer from server [{grab_product_count.doc.code}] {grab_product_count.doc.body}', task)
                return

            product_count_string_list = grab_product_count.doc.select('.//table[@class="productpickup_table"]//tbody/tr/td[last()]')
            product_count = None
            product_status = None
            total_count = 0

            for product_count_string in product_count_string_list:
                count = product_count_string.text('')
                count_number = Ree.extract_int.match(count)

                # just check if
                if count_number:
                    total_count += int(count_number.groupdict()['int'])

                elif count == 'В наличии':
                    product_count = '-1'
                    product_status = '0'

                elif count == 'Уточняйте у менеджера':
                    product_count = '-1'
                    product_status = '-1'

                elif count == 'Под заказ':
                    return

            # set value if was number
            if total_count > 0:
                # warn if different statuses
                if product_count:
                    self.log_warn(SC.MSG_POSSIBLE_WARN, f'Inconsistent count: total = {total_count}, product_count = {product_count}', task)

                product_count = str(total_count)
                product_status = '0'

            # check if valid
            if product_count is None or product_status is None:
                self.log_warn(SC.MSG_UNKNOWN_STATUS, 'Empty status!', task)
                return

            # D = unit (measure)
            product_unit = product_info.select('.//div[@class="input units"]').text('ед.')

            # E = price
            product_price = product_info.select('.//span[@itemprop="price"]').attr('content', '')

            if not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # F = vendor code (sku)
            product_vendor_table = product_info.select('.//div[@class="proditemcode"]')
            product_vendor_code = None

            for product_vendor_info in product_vendor_table:
                key = product_vendor_info.select('./text()').text('')

                if key == 'Артикул:':
                    product_vendor_code = product_vendor_info.select('./span').text('')

            if not product_vendor_code:
                self.log_warn(SC.MSG_UNKNOWN_SKU, 'Empty!', task)

            # G = vendor (manufacture)
            product_vendor = product_info.select('.//a[@itemprop="brand"]').attr('content', '')

            # H = photo url
            product_photo_url_raw = product_info.select('.//a[@itemprop="image"]').attr('href', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # I = description (properties)
            product_description = {}

            table = product_info.select('.//table[@id="product-features"]//tr')

            for row in table:
                key = row.select('./td[@class="name"]').text('')
                value = row.select('./td[@class="value"]').text('')

                if key:
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
                'properties': product_description,
                'id': product_id,
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
