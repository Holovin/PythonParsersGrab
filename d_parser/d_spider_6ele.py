from d_parser.d_spider_common import DSpiderCommon
from d_parser.helpers.re_set import Ree
from helpers.url_generator import UrlGenerator


VERSION = 28


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(DSpiderCommon):
    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number, try_limit)

    # fetch categories
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                self.log.fatal(task, f'Err task, attempt {task.task_try_count}')
                return

            # catalog
            catalog = grab.doc.select('//div[@id="js_ajax-catalog"]')

            # parse items
            items_list = catalog.select('.//a[@class="bx_rcm_view_link"]')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_item', link, 100, last=True)

            # parse next page link
            next_page = catalog.select('.//a[@title="След."]').attr('href', '')

            if next_page:
                next_page = UrlGenerator.get_page_params(self.domain, next_page, {})
                yield self.do_task('initial', next_page, 90, last=False)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse single item
    def task_parse_item(self, grab, task):
        try:
            # skip bad 404 links, i don't know how it occurs
            if grab.doc.code == 404:
                self.log.info(task, 'Start'.format(task.url))
                self.info.add(grab.doc.code)

                self.log.info(task, 'Skip task, 404...')
                return

            if self.check_body_errors(grab, task):
                yield self.check_errors(task, last=True)
                return

            # common block with info
            product_info = grab.doc.select('//div[contains(@class, "rs_detail rs_product")]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1/text()').text()

            # B = count (quantity)
            # C = status (delivery)
            product_count_string = product_info.select('.//span[@class="rs_stock-amount"]').text('')

            if product_count_string == 'Есть':
                product_count = '-1'
                product_status = '0'

            elif product_count_string == 'Мало':
                product_count = '-1'
                product_status = '0'

            elif product_count_string == 'Нет':
                product_count = '-1'
                product_status = '-1'

            else:
                self.log.warning(task, f'Unknown count status {product_count_string} skip...')
                return

            # D = unit (measure)
            product_unit = product_info.select('.//span[@class="js_measurename"]').text('ед.')

            # E = price
            product_price = product_info.select('.//span[@class="rs_prices-pdv js_price_pdv-1"]').text('').replace(' руб.', '')

            if not product_price or not Ree.float.match(product_price):
                self.log.warning(task, f'Unknown price status {product_price}, skip...')
                return

            # F = vendor code (sku)
            product_vendor_code = product_info.select('.//span[@class="rs_product-article"]/span[2]').text('')

            # G = vendor (manufacture) [const]
            product_vendor = 'EKF'

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[@class="preview-wrap"][1]/img[@class="preview"]').attr('src', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # I = description (properties)
            product_description = {}

            # try parse full props
            table_keys = product_info.select('.//div[@id="rs_detail-props"]//dt')
            table_values = product_info.select('.//div[@id="rs_detail-props"]//dd')

            if table_keys and table_values:
                for index, row_keys in enumerate(table_keys):
                    product_description[row_keys.text('')] = table_values[index].text('')

            else:
                table_keys = product_info.select('.//dl[@class="rs_list"]/dt')
                table_values = product_info.select('.//dl[@class="rs_list"]/dd')

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
