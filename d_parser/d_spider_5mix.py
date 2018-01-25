import re

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init, check_errors, extend_class, process_finally
from d_parser.helpers.re_set import Ree
from helpers.config import Config
from helpers.url_generator import UrlGenerator


VERSION = 27


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
                self.log.fatal(task, f'Err task, attempt {task.task_try_count}')
                return

            links = grab.doc.select('//nav//a[re:match(@href, "/product_list/.+/.+/.+/")]')

            for link in links:
                url = UrlGenerator.get_page_params(self.domain, link.attr('href'), {'count': 999999, 'name': 'asc'})
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
            product_count = '-1'

            # E = price
            # if E = "запросить цену и наличие" => -1
            # else => float
            product_price_raw = product_info.select('.//div[@class="cupit"]')

            if 'запросить' in product_price_raw.text() and product_count_string == 'В наличии':
                # C = status
                # if B = "в наличии" => 0
                product_status = '0'
                product_price = '-1'

            else:
                # E = price (float)
                product_price = product_info.select('.//div[@class="cupit"]/div[1]/span/following-sibling::text()[1]').text(default='[not found]')

                # check if correct price
                if not Ree.float.match(product_price):
                    self.log.warning(task, f'Skip item, cuz wrong price {product_price}')
                    return

                # C = status
                # if B = "в наличии" => 000000000
                # if B = "Под заказ 1-3 дня" => zakaz3
                # if B = "Под заказ 12 дней" => zakaz12
                # if B = "Под заказ 9 дней" => zakaz9
                if product_count_string == 'В наличии':
                    product_status = '0'

                elif product_count_string == 'Под заказ, 1-3 дня' \
                        or product_count_string == 'Под заказ, 2 дня'\
                        or product_count_string == 'Под заказ, 3 дня'\
                        or product_count_string == 'Под заказ, 1 день':
                    product_status = '3'

                elif product_count_string == 'Под заказ, 12 дней':
                    product_status = '12'

                elif product_count_string == 'Под заказ, 9 дней':
                    product_status = '9'

                else:
                    self.log.warning(task, f'Skip because {product_count_string} is unknown status')
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

            # I = description
            product_description_raw = grab.doc.select('//div[@class="tabs"]/div/div')

            product_description = {'Описание': product_description_raw.select('./div[2]/p').text()}

            table = product_description_raw.select('./div[1]//tr')

            for row in table:
                key = row.select('./td[1]').text().strip(':')
                value = row.select('./td[2]').text()

                if key:
                    product_description[key] = value

            # save
            row = {
                'name': product_name,
                'quantity': product_count,
                'delivery': product_status,
                'measure': product_unit,
                'price': product_price,
                'sku': product_vendor_code,
                'manufacture': product_vendor,
                'photo': product_photo_url,
                'properties': product_description
            }

            self.log.info(task, row)
            self.result.append(row)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
