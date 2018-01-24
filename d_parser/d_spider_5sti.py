import re

from grab.spider import Spider, Task

from d_parser.helpers.cookies_init import cookies_init
from d_parser.helpers.parser_extender import check_body_errors, process_error, common_init, extend_class, check_errors, process_finally
from helpers.config import Config
from helpers.url_generator import UrlGenerator


VERSION = 27


# Warn: Don't remove task argument even if not use it (it's break grab and spider crashed)
# Warn: noinspection PyUnusedLocal
class DSpider(Spider):
    initial_urls = Config.get_seq('SITE_URL')
    re_product_count = re.compile('^.+: (?P<count>\d+)$')
    re_product_price = re.compile('^.+:\s+(?P<price>\d+(.+\d)?).+$')

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

    # Fetch all categories from main page
    def task_initial(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                self.log.fatal(task, f'Err task, attempt {task.task_try_count}')
                return

            exclude_links_labels = ['Оплата', 'Доставка', 'Гарантия', 'Акции', 'Рекомендации по подбору', 'Информация и реквизиты',
                                    'Новости', 'Контакты', 'Сервис-центр']

            # take all links from horizontal nav, exclude anchors (#) and external links
            category_list = grab.doc.select('//div[@id="navbar"]//a[starts-with(@href, "/")]')

            # take links only for main cats, because its already contain all sub-cats items
            for link in category_list:
                # skip if label have stop words
                if link.text().strip() in exclude_links_labels:
                    continue

                link = link.attr('href')

                # make absolute urls if needed
                if link[:1] == '/':
                    link = UrlGenerator.get_page_params(self.domain, link, {})

                yield Task('parse_page', url=link, priority=90, raw=True)

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse page
    def task_parse_page(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)

            # parse items
            items_list = grab.doc.select('//div[@class="prod-list-cell"]//a[.!=""]')

            for index, row in enumerate(items_list):
                link = row.attr('href')

                # make absolute urls if needed
                if link[:1] == '/':
                    link = UrlGenerator.get_page_params(self.domain, link, {})

                yield Task('parse_item', url=link, priority=100, raw=True)

        except Exception as e:
            self._process_error(grab, task, e)

        finally:
            self.process_finally(task)

    # parse single item
    def task_parse_item(self, grab, task):
        try:
            if self.check_body_errors(grab, task):
                yield self.check_errors(task)

            # parse fields
            # A = name
            product_name = grab.doc.select('//h1').text()

            # B = count
            # C = status
            product_count_string = grab.doc.select('//span[@class="p-qty-wh"]').text()

            if product_count_string == 'Под заказ':
                product_status = '-1'
                product_count = '-1'

            elif product_count_string == 'На складе: более 100':
                product_status = '-1'
                product_count = 100

            else:
                product_status = '-1'
                product_count = DSpider.re_product_count.match(product_count_string).groupdict()['count']

            # D = unit [const = value]
            product_unit = 'ед.'

            # E = price
            product_price = DSpider.re_product_price.match(grab.doc.select('//div[@class="ppage-product-price"]').text()).groupdict()['price'].replace(' ', '')

            # check if positive and correct price
            if not product_price.isdigit():
                self.log.debug(task, f'Skip item, cuz wrong price {product_price}')
                return

            # F = vendor code [const = skip for parsing]
            product_vendor_code = ''

            # G = vendor [const = value]
            product_vendor = 'Stiebel Eltron'

            # H = photo url
            product_photo_url = UrlGenerator.get_page_params(self.domain, grab.doc.select('//img[@id="Image1"]').attr('src'), {})

            # I = description
            product_description = {'ОБЛАСТЬ ПРИМЕНЕНИЯ': grab.doc.select('//div[@class="col-md-14"]/p').text(default=' ')}

            table = grab.doc.select('//div[@class="col-md-14"]/table//tr')

            for row in table:

                key = row.select('./td[1]').text()
                value = row.select('./td[2]').text()

                if key:
                    product_description[key] = value

            # save
            self.result.append({
                'name': product_name,
                'quantity': product_count,
                'delivery': product_status,
                'measure': product_unit,
                'price': product_price,
                'sku': product_vendor_code,
                'vendor': product_vendor,
                'photo': product_photo_url,
                'properties': product_description
            })

        except Exception as e:
            self.process_error(grab, task, e)

        finally:
            self.process_finally(task)
