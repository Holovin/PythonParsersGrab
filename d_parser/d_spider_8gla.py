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

            items_list = grab.doc.select('//div[@class="menu"]//ul[not(@class="left_ul disp")]/li/a')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {'limit': 9999})
                yield self.do_task('parse_page', link,  DSpider.get_next_task_priority(task))

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

            items_list = grab.doc.select('//div[@class="catalog-blocks"]//div[@class="item"]')

            for item in items_list:
                state = item.select('.//div[@class="state"]').text('')

                # skip if wrong
                if not state or state != 'Есть в наличии':
                    if state not in ['Предзаказ']:
                        self.log_warn(SC.MSG_POSSIBLE_WARN, f'Wrong state "{state}"', task)

                    continue

                link = item.select('.//a[@class="name"]')
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
            product_info = grab.doc.select('//div[@class="item-blocks"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # Table B+C, F, G:
            table_info = product_info.select('.//div[@class="info"]/span')

            product_vendor = ''
            product_vendor_code = ''
            product_count = None
            product_status = None

            for row in table_info:
                value = row.text('')

                if value:
                    # G = vendor (manufacture)
                    if 'Производитель: ' in value:
                        product_vendor = value.replace('Производитель: ', '')

                    # F = vendor code (sku)
                    elif 'Артикул: ' in value:
                        product_vendor_code = value.replace('Артикул: ', '')

                    # B = count (quantity)
                    # C = status (delivery)
                    # (!double check!)
                    elif 'Наличие: ' in value:
                        if 'Есть в наличии' in value:
                            product_count = '-1'
                            product_status = '0'
                        else:
                            self.log_warn(SC.MSG_UNKNOWN_STATUS, f'Must be in stock, but receive wrong status "{value}"!', task)
                            return

            if not product_count or not product_status:
                self.log_warn(SC.MSG_UNKNOWN_STATUS, f'Empty status/count values!!!', task)
                return

            # D = unit (measure) [const]
            product_unit = 'ед.'

            # E = price
            product_price = product_info.select('.//span[@class="price-big bk_price"]').text('').replace(' р.', '').replace(' ', '')

            if not product_price or not Ree.float.match(product_price):
                self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Unknown price status {product_price}, skip...', task)
                return

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[@class="image_box"]/a').attr('href', '')

            if product_photo_url_raw:
                product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})
            else:
                product_photo_url = ''

            # Description tabs
            desc_tabs = grab.doc.select('//div[@class="tabs-block"]')

            # I = description (properties)
            product_description = {
                'Описание': desc_tabs.select('.//section[@id="content1"]').text('')
            }

            # I [part 2]
            table = desc_tabs.select('.//section[@id="content2"]/span')

            for row in table:
                key = row.select('./span').text('').rstrip(':')
                value = row.select('./text()').text('')

                if key:
                    product_description[key] = value

            # ID
            product_id = product_info.select('.//input[@name="product_id"]').attr('value', '')

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
                'properties': product_description,
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
