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

            # parse cats
            categories_list = grab.doc.select('//ul[@class="tabs_catalog asd2"]//a')

            for link in categories_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_page', link, 90)

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

            # parse items links
            items_list = grab.doc.select('//div[@class="catalog-section-it-table-body"]//a')

            for link in items_list:
                link = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})

                yield self.do_task('parse_item', link, 100, last=True)

            # parse next page if current is ok
            next_page = grab.doc.select('//a[@class="catalog-pagenav-next"]').attr('href', '')

            if next_page:
                next_page = UrlGenerator.get_page_params(self.domain, next_page, {})
                yield self.do_task('parse_page', next_page, 90)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse single item
    def task_parse_item(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            # common block with info
            product_info = grab.doc.select('//div[@class="catalog-detail"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = count (quantity)
            # C = status (delivery)
            product_count_string = product_info.select('.//div[@class="item-is-available"]/span').text('')

            # D = unit (measure) [const if no stock, else parse]
            product_unit = ''

            if product_count_string:
                if product_count_string[-1] == 'м':
                    product_unit = 'м'
                    product_count_string = product_count_string[:-1].strip()

                elif product_count_string[-2:] == 'шт':
                    product_unit = 'шт'
                    product_count_string = product_count_string[:-2].strip()

                elif product_count_string[-2:] == 'уп':
                    product_unit = 'уп'
                    product_count_string = product_count_string[:-2].strip()

            if not product_unit:
                product_unit = 'ед.'

            if Ree.float.match(product_count_string):
                product_count = product_count_string
                product_status = '0'

            elif product_count_string == 'Ожидается поставка':
                product_count = '-1'
                product_status = '-1'

            else:
                self.log.warning(task, f'Unknown count status {product_count_string}, skip...')
                return

            # E = price
            product_price_raw = product_info.select('.//span[@class="item-know-price"]').text('')

            # need clarify
            if product_price_raw:
                product_price = '-1'

            # try get
            else:
                product_price_raw = product_info.select('.//span[@class="price__number"]').text('')

                if not product_price_raw or not Ree.float.match(product_price_raw):
                    self.log.warning(task, f'Unknown price status {product_price_raw}, skip...')
                    return

                product_price = product_price_raw

            # F = vendor code (sku) [const]
            product_vendor_code = ''

            # G = vendor (manufacture) [const]
            product_vendor = ''

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[@class="item-picture"]/a').attr('href')
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})

            # I = description (properties)
            product_description = {
                'Применение': product_info.select('.//div[@data-tabs-content-id="USAGE"]').text(''),
                'Технические характеристики': product_info.select('.//div[@data-tabs-content-id="TECH_SPECS"]').text(''),
                'Конструкция': product_info.select('.//div[@data-tabs-content-id="CONSTRUCTION"]').text(''),
            }

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
