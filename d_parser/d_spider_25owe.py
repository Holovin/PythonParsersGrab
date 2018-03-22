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

    # parse categories
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)
                return

            links = grab.doc.select('//div[@class="gsections"]//ul//a')

            for link in links:
                url = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield self.do_task('parse_page', url, DSpider.get_next_task_priority(task))

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
            items_links = grab.doc.select('//div[@class="catalog"]//div[@class="header"]//a')

            for row in items_links:
                link = row.attr('href')
                link = UrlGenerator.get_page_params(self.domain, link, {})

                yield self.do_task('parse_item', link, DSpider.get_next_task_priority(task))

            # parse next page
            items_next_page = grab.doc.select('//div[@class="pagination"]//a[contains(@class, "nextpage")]')

            for row in items_next_page:
                link = row.attr('href')
                link = UrlGenerator.get_page_params(self.domain, link, {})

                yield self.do_task('parse_page', link, DSpider.get_next_task_priority(task, 0))

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
            product_info = grab.doc.select('//div[@class="textblock"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = [const]
            product_count = '-1'

            # C = depends on B [in stock / pod zakaz]
            product_count_string = product_info\
                .select('.//div[@class="priceblock"]/div[2]/span/following-sibling::text()[1]')\
                .text(default='[not found]').strip()

            if product_count_string == 'есть в наличии':
                product_status = '0'

            elif product_count_string == 'под заказ':
                product_status = '-1'

            else:
                self.log_warn(SC.MSG_UNKNOWN_COUNT, f'Skip item, cuz wrong count {product_count_string}', task)
                return

            # D = unit
            product_unit = product_info.select('.//div[@class="countblock"]/p[@class="p2"]').text()

            if product_unit == '':
                product_unit = 'ед.'

            # E = price
            # if E = "запросить цену и наличие" => -1
            # else => float
            product_price = product_info.select('.//div[@class="priceblock"]//span[1]')\
                .text(default='').strip().replace(' ', '')

            if product_price == 'Позапросу':
                product_price = '-1'

            else:
                # E = price (float)
                # check if correct price
                if not Ree.float.match(product_price):
                    self.log_warn(SC.MSG_UNKNOWN_PRICE, f'Skip item, cuz wrong price {product_price}', task)
                    return

            # F = vendor code
            product_vendor_code = product_info.select('.//div[@class="opt"]/p/span').text()

            # G = vendor [const empty]
            product_vendor = ' '

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[@class="img "]//img').attr('src')
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})

            # I = description [const empty]
            # part 1 -- table
            product_description_table = product_info.select('.//div[@class="descr"]//table').text(default='')

            # part 2 -- under table
            product_description_under_table = product_info.select('.//div[@class="descr"]/div[@class="text"]/p').text(default='')

            # part 3 -- technical data
            product_description_technical = product_info.select('.//div[@id="slide2"]').text(default='')

            # no newline in f-strings, python, really?
            product_description = {
                'Технические характеристики': '{}\n{}'.format(product_description_table, product_description_under_table),
                'Подробное описание': product_description_technical,
            }

            # ID
            product_id = product_info.select('.//input[@name="shk-id"]').attr('value', '')

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
