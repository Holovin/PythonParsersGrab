import re

from grab.spider import Spider, Task
from weblib.error import DataNotFound

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
    re_product_unit = re.compile('^.+\d\s(?P<unit>.+)$')

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
                return

            links = grab.doc.select('//nav//a[re:match(@href, "/product_list/.+/.+/.+/")]')

            for link in links:
                url = UrlGenerator.get_page_params(self.domain, link.attr('href'), {'count': 99999, 'name': 'asc'})
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

            # parse items links                         # yep, with u letter
            items_links = grab.doc.select('//div[@class="pruduct_grid"]//a[@class="pruduct_grid_title"]')

            for index, row in enumerate(items_links):
                link = row.attr('href')

                # make absolute urls if needed
                if link[:1] == '/':
                    link = UrlGenerator.get_page_params(self.domain, link, {})

                yield Task('parse_item', url=link, priority=100, raw=True)

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
            product_info = grab.doc.select('//div[@class="item_good"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = [const]
            product_count_string = product_info.select('.//div[@class="availability"]').text()
            product_count = 'zapros'

            # E = price
            # if E = "запросить цену и наличие" => zapros
            # else => float
            product_price_raw = product_info.select('.//div[@class="cupit"]')

            if 'запросить' in product_price_raw.text() and product_count_string == 'В наличии':
                # C = status
                # if B = "в наличии" => 000000000
                product_status = '000000000'
                product_price = 'zapros'

            else:
                # E = price (float)
                product_price = product_info.select('.//div[@class="cupit"]/div[1]/span/following-sibling::text()[1]').text(default='[not found]').strip()

                # check if correct price
                if not Ree.float.match(product_price):
                    self.log.warning(task, 'Skip item, cuz wrong price {}'.format(product_price))
                    return

                # C = status
                # if B = "в наличии" => 000000000
                # if B = "Под заказ 1-3 дня" => zakaz3
                # if B = "Под заказ 12 дней" => zakaz12
                # if B = "Под заказ 9 дней" => zakaz9
                if product_count_string == 'В наличии':
                    product_status = '000000000'

                elif product_count_string == 'Под заказ, 1-3 дня':
                    product_status = 'zakaz3'

                elif product_count_string == 'Под заказ, 12 дней':
                    product_status = 'zakaz12'

                elif product_count_string == 'Под заказ, 9 дней':
                    product_status = 'zakaz9'

                else:
                    self.log.warning(task, 'Skip because {} is unknown status'.format(product_count_string))
                    return

            # D = unit
            product_unit = product_info.select('.//div[@class="unit"]').text()

            if product_unit == '':
                product_unit = 'ед.'

            # F = vendor code
            product_vendor_code = product_info.select('.//p/span[1]/span[1]').text()

            # G = vendor
            product_vendor = product_info.select('.//p/span[2]/span[1]').text()

            # H = photo url
            product_photo_url_raw = product_info.select('./div[@class="photo"]//img').attr('src')
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})

            # I = description [const empty]
            product_description = grab.doc.select('//div[@class="tabs"]').text()\
                .replace('вконтакт', '')\
                .replace('однокласники', '')\
                .replace('twitter', '')\
                .replace('facebook', '')\

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
