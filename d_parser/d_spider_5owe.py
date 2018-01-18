from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init, check_errors, extend_class, process_finally
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator


VERSION = 26


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')

    def __init__(self, thread_number, try_limit=0):
        super().__init__(thread_number=thread_number, network_try_limit=try_limit, priority_mode='const')

        extend_class(DSpider, [
            check_body_errors,
            check_errors,
            process_error,
            process_finally,
            common_init
        ])

        self.common_init(try_limit)

    def create_grab_instance(self, **kwargs):
        grab = super(DSpider, self).create_grab_instance(**kwargs)
        return cookies_init(self.cookie_jar, grab)

    # parse categories
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                self.log.fatal(task, 'Err task, attempt {}'.format(task.task_try_count))

            links = grab.doc.select('//div[@class="gsections"]//ul//a')

            for link in links:
                url = UrlGenerator.get_page_params(self.domain, link.attr('href'), {})
                yield Task('parse_page', url=url, priority=90, raw=True)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)

            # parse items links
            items_links = grab.doc.select('//div[@class="catalog"]//div[@class="header"]//a')

            for row in items_links:
                link = row.attr('href')
                link = UrlGenerator.get_page_params(self.domain, link, {})

                yield Task('parse_item', url=link, priority=100, raw=True)

            # parse next page
            items_next_page = grab.doc.select('//div[@class="pagination"]//a[contains(@class, "nextpage")]')

            for row in items_next_page:
                link = row.attr('href')
                link = UrlGenerator.get_page_params(self.domain, link, {})

                yield Task('parse_page', url=link, priority=90, raw=True)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse single item
    def task_parse_item(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)

            # common block with info
            product_info = grab.doc.select('//div[@class="textblock"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = [const]
            product_count = 'zapros'

            # C = depends on B [in stock / pod zakaz]
            product_count_string = product_info\
                .select('.//div[@class="priceblock"]/div[2]/span/following-sibling::text()[1]')\
                .text(default='[not found]').strip()

            if product_count_string == 'есть в наличии':
                product_status = '000000000'

            elif product_count_string == 'под заказ':
                product_status = 'zakaz'

            else:
                self.log.warning(task, 'Skip item, cuz wrong count {}'.format(product_count_string))
                return

            # D = unit
            product_unit = product_info.select('.//div[@class="countblock"]/p[@class="p2"]').text()

            if product_unit == '':
                product_unit = 'ед.'

            # E = price
            # if E = "запросить цену и наличие" => zapros
            # else => float
            product_price = product_info.select('.//div[@class="priceblock"]//span[1]')\
                .text(default='').strip().replace(' ', '')

            if product_price == 'Позапросу':
                product_price = 'zapros'

            else:
                # E = price (float)
                # check if correct price
                if not Ree.float.match(product_price):
                    self.log.warning(task, 'Skip item, cuz wrong price {}'.format(product_price))
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

            product_description = '{}\n{}\n{}'.format(
                product_description_table,
                product_description_under_table,
                product_description_technical,
            )

            # save
            row = {
                'name': product_name,
                'count': product_count,
                'status': product_status,
                'unit': product_unit,
                'price': product_price,
                'vendor_code': product_vendor_code,
                'vendor': product_vendor,
                'photo_url': product_photo_url,
                'description': product_description
            }

            self.log.info(task, row)
            self.result.append(row)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
