from grab.spider import Spider, Task
from lxml import html

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

            links = grab.doc.select('//div[@id="main-subitems"]//a')

            for link in links:
                url = UrlGenerator.get_page_params(self.domain, link.attr('href'), {'onpage': 99999})
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
            items_links = grab.doc.select('//div[@id="catalog-list"]//div[@class="catalog-items"]//a[@property="name"]')

            for row in items_links:
                link = row.attr('href')
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
            product_info = grab.doc.select('//div[@id="product-info"]')

            # parse fields
            # A = name
            product_name = product_info.select('.//h1').text()

            # B = [const]
            # C = [const]
            # D = [const]
            product_count_string = product_info.select('.//div[@class="product-data-storehouse"]').text(default='[not found]')
            product_count = '-1'
            product_status = '0'
            product_unit = 'ед.'

            if product_count_string != 'в наличии':
                self.log.warning(task, 'Skip item, cuz wrong count {}'.format(product_count_string))
                return

            # E = price
            # if E = "запросить цену и наличие" => zapros
            # else => float
            product_price = product_info.select('.//span[@itemprop="price"]').text().replace(' ', '')

            if product_price == 'Уточняйте':
                product_price = '-1'

            else:
                # E = price (float)
                # check if correct price
                if not Ree.float.match(product_price):
                    self.log.warning(task, f'Skip item, cuz wrong price {product_price}')
                    return

            # F = vendor code
            product_vendor_code = product_info.select('.//div[@class="product-data-articul"]').text()

            # G = vendor
            product_vendor = product_info.select('.//div[@class="product-data-producer"]').text()

            # H = photo url
            product_photo_url_raw = product_info.select('.//div[@id="product-images-list"]/div[1]/img[@itemprop="contentUrl"]').attr('src')
            product_photo_url = UrlGenerator.get_page_params(self.domain, product_photo_url_raw, {})

            # pre I
            product_description_part_raw = product_info.select('.//div[@class="product-description description"]/following-sibling::node()[2]')\
                .text(default='')\
                .replace('$(".description").html(\'', '')\
                .replace('\');', '')

            # I = description
            # this part insert pure html with js, so we need clear all html tags and &-symbols
            product_description_part_list = html.fromstring(f'<div>{product_description_part_raw}</div>').xpath('string()')
            product_description_part = ''

            for row in product_description_part_list:
                product_description_part += row

            product_description = {'Описание': product_description_part}

            table = product_info.select('.//div[@class="product-description table"]/div')

            for row in table:
                key = row.select('./text()').text()
                value = row.select('./span').text()

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
