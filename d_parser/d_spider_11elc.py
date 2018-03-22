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
            catalog = grab.doc.select('//div[@class="topcatalog"]//a[re:match(@href, "/.+/.+/")]')

            for link in catalog:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
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

            catalog = grab.doc.select('//div[@class="listcatalog"]')

            # generate new tasks
            links = catalog.select('.//div[@class="navigation"]/div[@class="nav"]//a')
            max_page = 1

            for link in links:
                page_number = link.text('')

                if page_number and Ree.number.match(page_number):
                    max_page = max(max_page, int(page_number))

            if max_page > 1:
                for page in range(2, max_page):
                    next_page = UrlGenerator.get_page_params(task.url, '', {'PAGEN_1': page})
                    yield self.do_task('parse_page_items', next_page, DSpider.get_next_task_priority(task, 0))

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page
    def task_parse_page_items(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            catalog = grab.doc.select('//div[@class="listcatalog"]')

            # parse items links
            items_list = catalog.select('.//table[@class="lclistitem"]//td[@class="name"]//a')

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
            # common block with info
            product_info = grab.doc.select('//div[@class="itemcatalog"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = count (quantity)
            # C = status (delivery)
            product_count_string = product_info.select('.//table[@id="hint-table"]//tr[1]//td[2]').text('')

            if product_count_string == 'Имеется в наличии':
                product_count = '-1'
                product_status = '0'

            elif product_count_string in ['Ожидается поступление', 'Под заказ']:
                product_count = '-1'
                product_status = '-1'

            else:
                self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Unknown count status {product_count_string} skip...', task)
                return

            # E = price
            product_price = product_info.select('.//span[@class="price"]').text('').replace(' руб.', '')

            if product_price == 'по запросу':
                product_price = '-1'

            if not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # H = photo url
            product_photo_url_raw = product_info.select('.//a[@itemprop="image"]').attr('href', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # I = description (properties)
            product_description = {}

            # default values
            product_unit = 'ед.'
            product_vendor_code = ''
            product_vendor = ''

            tin_tab = product_info.select('.//table[@class="tintab"]')

            # try parse full props
            for row in tin_tab.select('.//tr'):
                key = row.select('./td[1]').text('')
                value = row.select('./td[2]').text('')

                # D = unit (measure)
                if key == 'Единица измерения':
                    product_unit = value

                # F = vendor code (sku)
                elif key == 'Артикул':
                    product_vendor_code = value

                elif key == 'Торговая марка / производитель':
                    product_vendor = value

                # default save
                if key:
                    product_description[key] = value

            # common
            item_description_rows = grab.doc.select('//div[@itemprop="description"]')
            item_description = ''

            for row in item_description_rows:
                if row.node().tag not in ['table', 'img']:
                    item_description += row.text('')

            if item_description:
                product_description['Техническое описание'] = item_description

            # ID
            product_id = Ree.extract_int.match(product_info.select('.//a[@class="button orange itembtn butbasket"]').attr('id', ''))

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
